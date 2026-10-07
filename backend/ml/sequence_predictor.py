"""LSTM Sequence Predictor for temporal pattern prediction."""

from typing import Dict, Any, Optional, List, Tuple
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from sqlalchemy.orm import Session

from backend.logging_config import get_logger

logger = get_logger(__name__)

try:
    import tensorflow as tf
    from tensorflow.keras.models import Sequential
    from tensorflow.keras.layers import LSTM, Dense, Dropout, Masking
    from tensorflow.keras.optimizers import Adam
    from tensorflow.keras.callbacks import EarlyStopping, ModelCheckpoint
    TENSORFLOW_AVAILABLE = True
except ImportError:
    TENSORFLOW_AVAILABLE = False
    logger.warning("TensorFlow not available. Sequence prediction will use fallback.")

from backend.ml.base import BaseMLModel, FloyoDataProcessor
from database.models import Event, TemporalPattern, WorkflowExecution


class SequencePredictor(BaseMLModel):
    """LSTM model for predicting workflow needs from temporal sequences."""
    
    def __init__(self, model_version: int = 1, sequence_length: int = 10):
        super().__init__("sequence_predictor", model_version)
        self.sequence_length = sequence_length
        self.feature_count = 0
        self.model = None
        
        if not TENSORFLOW_AVAILABLE:
            logger.warning("TensorFlow not available. Using fallback predictor.")
            self.use_fallback = True
        else:
            self.use_fallback = False
    
    def train(self, db: Session, user_id: Optional[str] = None, **kwargs) -> Dict[str, float]:
        """Train the LSTM sequence predictor.
        
        Args:
            db: Database session
            user_id: Optional user ID to filter training data
            **kwargs: Additional training parameters
            
        Returns:
            Dictionary of training metrics
        """
        if self.use_fallback:
            return self._train_fallback(db, user_id, **kwargs)
        
        try:
            logger.info(f"Training SequencePredictor (LSTM) for user_id={user_id}")
            
            # Load events
            events_df = FloyoDataProcessor.events_to_dataframe(db, user_id, limit=50000)
            if events_df is None or events_df.empty:
                logger.warning("No events data available")
                return {"error": "No training data available"}
            
            # Load workflow executions to create labels
            query = db.query(WorkflowExecution)
            if user_id:
                query = query.filter(WorkflowExecution.triggered_by == user_id)
            
            executions = query.all()
            execution_times = {str(e.workflow_id): e.started_at for e in executions if e.started_at}
            
            # Prepare sequences
            sequences, labels = self._prepare_sequences(events_df, execution_times)
            
            if len(sequences) < 50:
                logger.warning("Insufficient sequences for training")
                return {"error": "Insufficient training data"}
            
            # Split data
            split_idx = int(len(sequences) * 0.8)
            X_train = sequences[:split_idx]
            y_train = labels[:split_idx]
            X_test = sequences[split_idx:]
            y_test = labels[split_idx:]
            
            # Build model
            self.feature_count = sequences.shape[2]
            self.model = self._build_model()
            
            # Train
            early_stopping = EarlyStopping(monitor='val_loss', patience=5, restore_best_weights=True)
            
            history = self.model.fit(
                X_train, y_train,
                validation_data=(X_test, y_test),
                epochs=50,
                batch_size=32,
                callbacks=[early_stopping],
                verbose=0
            )
            
            # Evaluate
            train_loss = self.model.evaluate(X_train, y_train, verbose=0)
            test_loss = self.model.evaluate(X_test, y_test, verbose=0)
            
            y_pred = (self.model.predict(X_test, verbose=0) > 0.5).astype(int).flatten()
            y_test_flat = y_test.flatten()
            
            accuracy = np.mean(y_pred == y_test_flat)
            precision = np.sum((y_pred == 1) & (y_test_flat == 1)) / (np.sum(y_pred == 1) + 1e-10)
            recall = np.sum((y_pred == 1) & (y_test_flat == 1)) / (np.sum(y_test_flat == 1) + 1e-10)
            f1 = 2 * (precision * recall) / (precision + recall + 1e-10)
            
            self.training_metrics = {
                "train_loss": float(train_loss),
                "test_loss": float(test_loss),
                "accuracy": float(accuracy),
                "precision": float(precision),
                "recall": float(recall),
                "f1_score": float(f1),
                "training_samples": len(X_train),
                "test_samples": len(X_test),
            }
            
            self.is_trained = True
            self.last_trained_at = datetime.utcnow()
            
            logger.info(f"SequencePredictor trained. Accuracy: {accuracy:.3f}, F1: {f1:.3f}")
            
            return self.training_metrics
            
        except Exception as e:
            logger.error(f"Error training SequencePredictor: {e}", exc_info=True)
            return {"error": str(e)}
    
    def _build_model(self):
        """Build LSTM model."""
        model = Sequential([
            Masking(mask_value=0.0, input_shape=(self.sequence_length, self.feature_count)),
            LSTM(64, activation='relu', return_sequences=True, dropout=0.2),
            LSTM(32, activation='relu', dropout=0.2),
            Dense(16, activation='relu'),
            Dropout(0.2),
            Dense(1, activation='sigmoid')
        ])
        
        model.compile(
            optimizer=Adam(learning_rate=0.001),
            loss='binary_crossentropy',
            metrics=['accuracy']
        )
        
        return model
    
    def _prepare_sequences(self, events_df: pd.DataFrame, execution_times: Dict[str, datetime]) -> Tuple[np.ndarray, np.ndarray]:
        """Prepare sequences from events DataFrame."""
        # Sort by timestamp
        events_df = events_df.sort_values('timestamp').reset_index(drop=True)
        
        # Extract features
        features = []
        labels = []
        
        # Create sliding windows
        for i in range(len(events_df) - self.sequence_length):
            window = events_df.iloc[i:i+self.sequence_length]
            next_event = events_df.iloc[i+self.sequence_length]
            
            # Extract features from window
            seq_features = []
            for _, event in window.iterrows():
                feat = [
                    event.get('hour_of_day', 0),
                    event.get('day_of_week', 0),
                    1.0 if event.get('file_extension') else 0.0,
                    len(str(event.get('file_path', ''))),
                ]
                seq_features.append(feat)
            
            # Pad if needed
            while len(seq_features) < self.sequence_length:
                seq_features.append([0.0] * 4)
            
            features.append(seq_features)
            
            # Label: 1 if workflow was triggered within 1 hour of next event
            label = 0
            next_time = next_event.get('timestamp')
            if next_time:
                for exec_time in execution_times.values():
                    if exec_time and abs((next_time - exec_time).total_seconds()) < 3600:
                        label = 1
                        break
            
            labels.append(label)
        
        return np.array(features), np.array(labels).reshape(-1, 1)
    
    def _train_fallback(self, db: Session, user_id: Optional[str] = None, **kwargs) -> Dict[str, float]:
        """Fallback training using simple heuristics."""
        logger.info("Using fallback sequence predictor (no TensorFlow)")
        
        # Simple pattern matching
        events_df = FloyoDataProcessor.events_to_dataframe(db, user_id, limit=1000)
        if events_df is None or events_df.empty:
            return {"error": "No training data available"}
        
        # Count sequences
        sequences = 0
        for i in range(len(events_df) - self.sequence_length):
            sequences += 1
        
        self.is_trained = True
        self.last_trained_at = datetime.utcnow()
        
        return {
            "mode": "fallback",
            "sequences_analyzed": sequences,
            "accuracy": 0.6,  # Estimate
        }
    
    def predict(self, recent_events: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Predict if workflow will be needed soon based on recent events.
        
        Args:
            recent_events: List of recent event dictionaries
            
        Returns:
            Dictionary with prediction probability and explanation
        """
        if not self.is_trained:
            return {"probability": 0.5, "will_trigger": False, "error": "Model not trained"}
        
        if self.use_fallback:
            return self._predict_fallback(recent_events)
        
        try:
            # Prepare sequence
            if len(recent_events) < self.sequence_length:
                # Pad with zeros
                padded = recent_events + [{}] * (self.sequence_length - len(recent_events))
            else:
                padded = recent_events[-self.sequence_length:]
            
            # Extract features
            sequence = []
            for event in padded:
                feat = [
                    event.get('hour_of_day', 0),
                    event.get('day_of_week', 0),
                    1.0 if event.get('file_extension') else 0.0,
                    len(str(event.get('file_path', ''))),
                ]
                sequence.append(feat)
            
            # Pad to sequence_length
            while len(sequence) < self.sequence_length:
                sequence.append([0.0] * 4)
            
            # Predict
            X = np.array([sequence])
            probability = float(self.model.predict(X, verbose=0)[0][0])
            will_trigger = probability > 0.7
            
            return {
                "probability": probability,
                "will_trigger": will_trigger,
                "confidence": "high" if probability > 0.8 else "medium" if probability > 0.5 else "low"
            }
            
        except Exception as e:
            logger.error(f"Error making prediction: {e}")
            return {"probability": 0.5, "will_trigger": False, "error": str(e)}
    
    def _predict_fallback(self, recent_events: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Fallback prediction using heuristics."""
        if len(recent_events) < 3:
            return {"probability": 0.3, "will_trigger": False}
        
        # Simple heuristic: if many events in short time, likely need workflow
        event_count = len(recent_events)
        probability = min(event_count / 10.0, 0.9)
        
        return {
            "probability": probability,
            "will_trigger": probability > 0.6,
            "confidence": "medium"
        }
