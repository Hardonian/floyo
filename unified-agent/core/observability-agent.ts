/**
 * Observability & Telemetry Layer
 * Maintains metrics endpoint and dashboard
 */

import { writeFileSync, existsSync, mkdirSync } from 'fs';
import { join } from 'path';

export interface TelemetryData {
  timestamp: string;
  endpoint: string;
  latency: number;
  statusCode: number;
  error?: string;
}

export interface MetricsSnapshot {
  timestamp: string;
  requests: {
    total: number;
    success: number;
    errors: number;
    errorRate: number;
  };
  latency: {
    p50: number;
    p95: number;
    p99: number;
    avg: number;
  };
  endpoints: Array<{
    path: string;
    count: number;
    avgLatency: number;
    errorRate: number;
  }>;
}

export class ObservabilityAgent {
  private workspacePath: string;
  private metricsPath: string;
  private telemetryData: TelemetryData[] = [];
  private maxDataPoints = 1000;

  constructor(workspacePath: string = process.cwd()) {
    this.workspacePath = workspacePath;
    this.metricsPath = join(workspacePath, 'admin', 'metrics.json');
  }

  /**
   * Record telemetry data point
   */
  record(data: TelemetryData): void {
    this.telemetryData.push(data);

    // Keep only recent data
    if (this.telemetryData.length > this.maxDataPoints) {
      this.telemetryData = this.telemetryData.slice(-this.maxDataPoints);
    }
  }

  /**
   * Generate metrics snapshot
   */
  generateSnapshot(): MetricsSnapshot {
    const snapshot: MetricsSnapshot = {
      timestamp: new Date().toISOString(),
      requests: {
        total: this.telemetryData.length,
        success: 0,
        errors: 0,
        errorRate: 0,
      },
      latency: {
        p50: 0,
        p95: 0,
        p99: 0,
        avg: 0,
      },
      endpoints: [],
    };

    if (this.telemetryData.length === 0) {
      return snapshot;
    }

    // Calculate request metrics
    const successful = this.telemetryData.filter((d) => d.statusCode < 400);
    const errors = this.telemetryData.filter((d) => d.statusCode >= 400);

    snapshot.requests.success = successful.length;
    snapshot.requests.errors = errors.length;
    snapshot.requests.errorRate = errors.length / this.telemetryData.length;

    // Calculate latency metrics
    const latencies = this.telemetryData.map((d) => d.latency).sort((a, b) => a - b);
    snapshot.latency.p50 = this.percentile(latencies, 50);
    snapshot.latency.p95 = this.percentile(latencies, 95);
    snapshot.latency.p99 = this.percentile(latencies, 99);
    snapshot.latency.avg =
      latencies.reduce((a, b) => a + b, 0) / latencies.length;

    // Calculate per-endpoint metrics
    const endpointMap = new Map<string, TelemetryData[]>();
    for (const data of this.telemetryData) {
      if (!endpointMap.has(data.endpoint)) {
        endpointMap.set(data.endpoint, []);
      }
      endpointMap.get(data.endpoint)!.push(data);
    }

    for (const [path, data] of endpointMap.entries()) {
      const endpointErrors = data.filter((d) => d.statusCode >= 400);
      const endpointLatencies = data.map((d) => d.latency);

      snapshot.endpoints.push({
        path,
        count: data.length,
        avgLatency:
          endpointLatencies.reduce((a, b) => a + b, 0) / endpointLatencies.length,
        errorRate: endpointErrors.length / data.length,
      });
    }

    return snapshot;
  }

  /**
   * Save metrics snapshot
   */
  saveSnapshot(snapshot: MetricsSnapshot): void {
    const adminDir = join(this.workspacePath, 'admin');
    if (!existsSync(adminDir)) {
      mkdirSync(adminDir, { recursive: true });
    }

    writeFileSync(
      this.metricsPath,
      JSON.stringify(snapshot, null, 2),
      'utf-8'
    );
  }

  /**
   * Check for regressions (3 consecutive)
   */
  checkRegressions(_threshold: number = 3): boolean {
    // Would check historical snapshots
    // For now, return false
    return false;
  }

  /**
   * Calculate percentile
   */
  private percentile(sorted: number[], p: number): number {
    if (sorted.length === 0) {
      return 0;
    }
    const index = Math.ceil((p / 100) * sorted.length) - 1;
    return sorted[Math.max(0, index)];
  }
}
