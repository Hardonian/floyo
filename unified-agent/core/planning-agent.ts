/**
 * Planning & Roadmap Agent
 * Extracts TODOs/FIXMEs and generates sprint plans
 */

import { writeFileSync, existsSync, readFileSync, mkdirSync } from 'fs';
import { readdirSync, statSync } from 'fs';
import { join } from 'path';
import type { RepoContext } from './repo-context.js';

export interface TodoItem {
  file: string;
  line: number;
  type: 'TODO' | 'FIXME' | 'NOTE' | 'HACK';
  message: string;
  priority: 'high' | 'medium' | 'low';
}

export interface SprintPlan {
  timestamp: string;
  todos: TodoItem[];
  epics: Array<{
    name: string;
    todos: TodoItem[];
    estimatedEffort: string;
  }>;
  milestones: Array<{
    name: string;
    targetDate: string;
    epics: string[];
  }>;
}

export class PlanningAgent {
  private workspacePath: string;
  private sprintPath: string;

  constructor(workspacePath: string = process.cwd()) {
    this.workspacePath = workspacePath;
    this.sprintPath = join(workspacePath, 'roadmap', 'current-sprint.md');
  }

  /**
   * Extract TODOs and generate sprint plan
   */
  async generateSprintPlan(_context: RepoContext): Promise<SprintPlan> {
    const plan: SprintPlan = {
      timestamp: new Date().toISOString(),
      todos: [],
      epics: [],
      milestones: [],
    };

    // Extract TODOs from codebase
    await this.extractTodos(plan);

    // Cluster into epics
    this.clusterIntoEpics(plan);

    // Generate milestones
    this.generateMilestones(plan);

    return plan;
  }

  /**
   * Extract TODO/FIXME comments from codebase
   */
  private async extractTodos(plan: SprintPlan): Promise<void> {
    const extensions = ['.ts', '.tsx', '.js', '.jsx', '.py', '.rs', '.go'];
    const todoPatterns = [
      /TODO:?\s*(.+)/gi,
      /FIXME:?\s*(.+)/gi,
      /NOTE:?\s*(.+)/gi,
      /HACK:?\s*(.+)/gi,
    ];

    const scanDirectory = (dir: string): void => {
      try {
        const entries = readdirSync(dir);
        
        for (const entry of entries) {
          // Skip node_modules, .git, etc.
          if (entry.startsWith('.') || entry === 'node_modules' || entry === 'dist' || entry === 'build') {
            continue;
          }

          const fullPath = join(dir, entry);
          const stat = statSync(fullPath);

          if (stat.isDirectory()) {
            scanDirectory(fullPath);
          } else if (stat.isFile()) {
            const ext = entry.substring(entry.lastIndexOf('.'));
            if (extensions.includes(ext)) {
              this.scanFile(fullPath, todoPatterns, plan);
            }
          }
        }
      } catch (e) {
        // Ignore permission errors
      }
    };

    scanDirectory(this.workspacePath);
  }

  /**
   * Scan a file for TODOs
   */
  private scanFile(
    filePath: string,
    patterns: RegExp[],
    plan: SprintPlan
  ): void {
    try {
      const content = readFileSync(filePath, 'utf-8');
      const lines = content.split('\n');
      const relativePath = filePath.replace(this.workspacePath + '/', '');

      lines.forEach((line, index) => {
        for (let i = 0; i < patterns.length; i++) {
          const pattern = patterns[i];
          const match = line.match(pattern);
          
          if (match) {
            const type = i === 0 ? 'TODO' : i === 1 ? 'FIXME' : i === 2 ? 'NOTE' : 'HACK';
            const message = match[1].trim();
            
            plan.todos.push({
              file: relativePath,
              line: index + 1,
              type,
              message,
              priority: this.determinePriority(message),
            });
          }
        }
      });
    } catch (e) {
      // Ignore read errors
    }
  }

  /**
   * Determine priority from TODO message
   */
  private determinePriority(message: string): 'high' | 'medium' | 'low' {
    const lower = message.toLowerCase();
    
    if (lower.includes('critical') || lower.includes('urgent') || lower.includes('security')) {
      return 'high';
    } else if (lower.includes('important') || lower.includes('soon')) {
      return 'medium';
    } else {
      return 'low';
    }
  }

  /**
   * Cluster TODOs into epics based on file location
   */
  private clusterIntoEpics(plan: SprintPlan): void {
    const epicMap = new Map<string, TodoItem[]>();

    for (const todo of plan.todos) {
      // Extract epic name from file path (e.g., frontend/, backend/, etc.)
      const parts = todo.file.split('/');
      const epicName = parts.length > 1 ? parts[0] : 'general';

      if (!epicMap.has(epicName)) {
        epicMap.set(epicName, []);
      }
      epicMap.get(epicName)!.push(todo);
    }

    // Convert to epics
    for (const [name, todos] of epicMap.entries()) {
      plan.epics.push({
        name: name.charAt(0).toUpperCase() + name.slice(1),
        todos,
        estimatedEffort: this.estimateEffort(todos),
      });
    }
  }

  /**
   * Generate milestones
   */
  private generateMilestones(plan: SprintPlan): void {
    // Group epics by priority
    const highPriorityEpics = plan.epics.filter((e) =>
      e.todos.some((t) => t.priority === 'high')
    );

    if (highPriorityEpics.length > 0) {
      const nextWeek = new Date();
      nextWeek.setDate(nextWeek.getDate() + 7);

      plan.milestones.push({
        name: 'High Priority Sprint',
        targetDate: nextWeek.toISOString().split('T')[0],
        epics: highPriorityEpics.map((e) => e.name),
      });
    }

    // Medium priority milestone
    const mediumPriorityEpics = plan.epics.filter(
      (e) =>
        !highPriorityEpics.includes(e) &&
        e.todos.some((t) => t.priority === 'medium')
    );

    if (mediumPriorityEpics.length > 0) {
      const nextMonth = new Date();
      nextMonth.setMonth(nextMonth.getMonth() + 1);

      plan.milestones.push({
        name: 'Medium Priority Sprint',
        targetDate: nextMonth.toISOString().split('T')[0],
        epics: mediumPriorityEpics.map((e) => e.name),
      });
    }
  }

  /**
   * Estimate effort for todos
   */
  private estimateEffort(todos: TodoItem[]): string {
    const count = todos.length;
    if (count <= 3) {
      return '1-2 days';
    } else if (count <= 10) {
      return '1 week';
    } else {
      return '2+ weeks';
    }
  }

  /**
   * Save sprint plan
   */
  saveSprintPlan(plan: SprintPlan): void {
    const roadmapDir = join(this.workspacePath, 'roadmap');
    if (!existsSync(roadmapDir)) {
      mkdirSync(roadmapDir, { recursive: true });
    }

    // Save JSON
    const jsonPath = join(roadmapDir, 'current-sprint.json');
    writeFileSync(jsonPath, JSON.stringify(plan, null, 2), 'utf-8');

    // Generate markdown report
    const report = this.generateSprintReport(plan);
    writeFileSync(this.sprintPath, report, 'utf-8');
  }

  /**
   * Generate sprint report markdown
   */
  private generateSprintReport(plan: SprintPlan): string {
    let report = `# Current Sprint Plan

Generated: ${plan.timestamp}

## Summary
- Total TODOs: ${plan.todos.length}
- Epics: ${plan.epics.length}
- Milestones: ${plan.milestones.length}

## TODOs by Priority
- High: ${plan.todos.filter((t) => t.priority === 'high').length}
- Medium: ${plan.todos.filter((t) => t.priority === 'medium').length}
- Low: ${plan.todos.filter((t) => t.priority === 'low').length}

## Epics

`;

    for (const epic of plan.epics) {
      report += `### ${epic.name}\n\n`;
      report += `**Estimated Effort**: ${epic.estimatedEffort}\n\n`;
      report += `**TODOs**: ${epic.todos.length}\n\n`;

      const highPriority = epic.todos.filter((t) => t.priority === 'high');
      if (highPriority.length > 0) {
        report += `#### High Priority\n\n`;
        for (const todo of highPriority) {
          report += `- [ ] **${todo.type}** (${todo.file}:${todo.line}): ${todo.message}\n`;
        }
        report += '\n';
      }
    }

    report += `## Milestones\n\n`;
    for (const milestone of plan.milestones) {
      report += `### ${milestone.name}\n\n`;
      report += `- **Target Date**: ${milestone.targetDate}\n`;
      report += `- **Epics**: ${milestone.epics.join(', ')}\n\n`;
    }

    report += `---\n*Auto-generated by Unified Agent System*\n`;

    return report;
  }
}
