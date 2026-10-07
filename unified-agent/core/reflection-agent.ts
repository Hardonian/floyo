/**
 * Auto-Improvement & Reflection Loop
 * Self-evaluates and proposes optimizations
 */

import { writeFileSync, existsSync, readFileSync, mkdirSync } from 'fs';
import { join } from 'path';
import type { RepoContext } from './repo-context.js';

export interface ReflectionReport {
  timestamp: string;
  cycle: number;
  changes: {
    filesChanged: number;
    commits: number;
    timeSinceLastRun: string;
  };
  optimizations: Array<{
    category: string;
    suggestion: string;
    impact: 'high' | 'medium' | 'low';
    effort: 'low' | 'medium' | 'high';
  }>;
  metrics: {
    tokenEfficiency: number;
    buildLatency: number;
    previousBuildLatency?: number;
    improvement: number;
  };
  nextSteps: string[];
}

export class ReflectionAgent {
  private workspacePath: string;
  private nextStepsPath: string;
  private cycleCount: number = 0;

  constructor(workspacePath: string = process.cwd()) {
    this.workspacePath = workspacePath;
    this.nextStepsPath = join(workspacePath, 'auto', 'next-steps.md');
  }

  /**
   * Generate reflection report
   */
  async reflect(context: RepoContext): Promise<ReflectionReport> {
    this.cycleCount++;

    const report: ReflectionReport = {
      timestamp: new Date().toISOString(),
      cycle: this.cycleCount,
      changes: await this.analyzeChanges(),
      optimizations: [],
      metrics: {
        tokenEfficiency: 0,
        buildLatency: 0,
        improvement: 0,
      },
      nextSteps: [],
    };

    // Load previous metrics for comparison
    const previous = this.loadPreviousMetrics();

    // Analyze current metrics
    report.metrics = await this.analyzeMetrics(previous);

    // Generate optimizations
    this.generateOptimizations(report, context);

    // Generate next steps
    this.generateNextSteps(report);

    return report;
  }

  /**
   * Analyze changes since last run
   */
  private async analyzeChanges(): Promise<{
    filesChanged: number;
    commits: number;
    timeSinceLastRun: string;
  }> {
    // Would use git to analyze changes
    // For now, return defaults
    return {
      filesChanged: 0,
      commits: 0,
      timeSinceLastRun: '24 hours',
    };
  }

  /**
   * Analyze metrics
   */
  private async analyzeMetrics(previous?: ReflectionReport): Promise<{
    tokenEfficiency: number;
    buildLatency: number;
    previousBuildLatency?: number;
    improvement: number;
  }> {
    // Load reliability metrics
    const reliabilityPath = join(this.workspacePath, 'admin', 'reliability.json');
    let buildLatency = 0;

    if (existsSync(reliabilityPath)) {
      try {
        const reliability = JSON.parse(readFileSync(reliabilityPath, 'utf-8'));
        buildLatency = reliability.buildTime?.total || 0;
      } catch {
        // Ignore errors
      }
    }

    const previousBuildLatency = previous?.metrics.buildLatency;
    const improvement = previousBuildLatency
      ? ((previousBuildLatency - buildLatency) / previousBuildLatency) * 100
      : 0;

    return {
      tokenEfficiency: 85, // Would calculate from actual usage
      buildLatency,
      previousBuildLatency,
      improvement,
    };
  }

  /**
   * Generate optimization suggestions
   */
  private generateOptimizations(
    report: ReflectionReport,
    context: RepoContext
  ): void {
    // Suggest dependency updates
    report.optimizations.push({
      category: 'Dependencies',
      suggestion: 'Run dependency audit and update outdated packages',
      impact: 'medium',
      effort: 'low',
    });

    // Suggest build optimization
    if (report.metrics.buildLatency > 120) {
      report.optimizations.push({
        category: 'Build Performance',
        suggestion: 'Optimize build process - consider caching and parallel builds',
        impact: 'high',
        effort: 'medium',
      });
    }

    // Suggest code splitting for frontend
    if (context.hasFrontend) {
      report.optimizations.push({
        category: 'Frontend',
        suggestion: 'Review code splitting and lazy loading opportunities',
        impact: 'medium',
        effort: 'medium',
      });
    }

    // Suggest API optimization
    if (context.hasBackend) {
      report.optimizations.push({
        category: 'Backend',
        suggestion: 'Review API response caching and query optimization',
        impact: 'high',
        effort: 'medium',
      });
    }
  }

  /**
   * Generate next steps
   */
  private generateNextSteps(report: ReflectionReport): void {
    // High impact, low effort optimizations first
    const highImpactLowEffort = report.optimizations.filter(
      (o) => o.impact === 'high' && o.effort === 'low'
    );

    for (const opt of highImpactLowEffort) {
      report.nextSteps.push(`[HIGH IMPACT] ${opt.suggestion}`);
    }

    // Then high impact, medium effort
    const highImpactMediumEffort = report.optimizations.filter(
      (o) => o.impact === 'high' && o.effort === 'medium'
    );

    for (const opt of highImpactMediumEffort) {
      report.nextSteps.push(`[HIGH IMPACT] ${opt.suggestion}`);
    }

    // Add default steps if none
    if (report.nextSteps.length === 0) {
      report.nextSteps.push('Continue monitoring metrics');
      report.nextSteps.push('Review security compliance report');
      report.nextSteps.push('Update documentation as needed');
    }
  }

  /**
   * Load previous metrics
   */
  private loadPreviousMetrics(): ReflectionReport | undefined {
    const previousPath = join(this.workspacePath, 'auto', 'previous-reflection.json');
    if (!existsSync(previousPath)) {
      return undefined;
    }

    try {
      return JSON.parse(readFileSync(previousPath, 'utf-8'));
    } catch {
      return undefined;
    }
  }

  /**
   * Save reflection report
   */
  saveReflection(report: ReflectionReport): void {
    const autoDir = join(this.workspacePath, 'auto');
    if (!existsSync(autoDir)) {
      mkdirSync(autoDir, { recursive: true });
    }

    // Save JSON
    const jsonPath = join(autoDir, 'reflection.json');
    writeFileSync(jsonPath, JSON.stringify(report, null, 2), 'utf-8');

    // Save previous for comparison
    const previousPath = join(autoDir, 'previous-reflection.json');
    if (existsSync(jsonPath)) {
      const current = readFileSync(jsonPath, 'utf-8');
      writeFileSync(previousPath, current, 'utf-8');
    }

    // Generate markdown report
    const markdown = this.generateReflectionReport(report);
    writeFileSync(this.nextStepsPath, markdown, 'utf-8');
  }

  /**
   * Generate reflection report markdown
   */
  private generateReflectionReport(report: ReflectionReport): string {
    let content = `# Self-Reflection & Next Steps

Generated: ${report.timestamp}
Cycle: ${report.cycle}

## Changes Since Last Run
- Files Changed: ${report.changes.filesChanged}
- Commits: ${report.changes.commits}
- Time Since Last Run: ${report.changes.timeSinceLastRun}

## Performance Metrics
- Token Efficiency: ${report.metrics.tokenEfficiency}%
- Build Latency: ${report.metrics.buildLatency}s
${report.metrics.previousBuildLatency
  ? `- Previous Build Latency: ${report.metrics.previousBuildLatency}s
- Improvement: ${report.metrics.improvement > 0 ? '+' : ''}${report.metrics.improvement.toFixed(2)}%`
  : ''}

## Optimizations Identified

`;

    for (const opt of report.optimizations) {
      content += `### ${opt.category}\n\n`;
      content += `- **Suggestion**: ${opt.suggestion}\n`;
      content += `- **Impact**: ${opt.impact}\n`;
      content += `- **Effort**: ${opt.effort}\n\n`;
    }

    content += `## Next Steps\n\n`;
    for (let i = 0; i < report.nextSteps.length; i++) {
      content += `${i + 1}. ${report.nextSteps[i]}\n`;
    }

    content += `\n---\n*Auto-generated by Unified Agent System*\n`;

    return content;
  }
}
