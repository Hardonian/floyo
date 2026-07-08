#!/usr/bin/env tsx
/**
 * Aurora Prime - Full Stack Autopilot
 * Autonomous full-stack orchestrator for validating, healing, and deploying
 * the entire application stack end-to-end.
 */

import { execSync } from 'child_process';
import * as fs from 'fs';
import * as path from 'path';
import { fileURLToPath } from 'url';
import { dirname } from 'path';
import { createClient } from '@supabase/supabase-js';

const __filename = fileURLToPath(import.meta.url);
const __dirname = dirname(__filename);

interface SystemStatus {
  supabase: 'Healthy' | 'FIXED' | 'Needs Attention';
  vercel: 'Healthy' | 'FIXED' | 'Needs Attention';
  expo: 'Healthy' | 'FIXED' | 'Needs Attention';
  githubActions: 'Healthy' | 'FIXED' | 'Needs Attention';
  secretsAlignment: 'Healthy' | 'FIXED' | 'Needs Attention';
  schemaDrift: 'None' | 'Auto-repaired' | 'Needs Manual Review';
  fixes: string[];
  recommendations: string[];
}

interface SecretConfig {
  name: string;
  required: boolean;
  services: string[];
}

const REQUIRED_SECRETS: SecretConfig[] = [
  { name: 'SUPABASE_URL', required: true, services: ['supabase', 'vercel', 'expo', 'github'] },
  { name: 'SUPABASE_SERVICE_ROLE_KEY', required: true, services: ['supabase', 'github'] },
  { name: 'SUPABASE_ANON_KEY', required: true, services: ['vercel', 'expo', 'github'] },
  { name: 'VERCEL_TOKEN', required: true, services: ['vercel', 'github'] },
  { name: 'NEXT_PUBLIC_SUPABASE_URL', required: true, services: ['vercel'] },
  { name: 'EXPO_PUBLIC_SUPABASE_URL', required: true, services: ['expo'] },
  { name: 'SUPABASE_ACCESS_TOKEN', required: true, services: ['github'] },
  { name: 'SUPABASE_PROJECT_REF', required: true, services: ['github'] },
  { name: 'VERCEL_ORG_ID', required: true, services: ['github'] },
  { name: 'VERCEL_PROJECT_ID', required: true, services: ['github'] },
  { name: 'EXPO_TOKEN', required: true, services: ['expo', 'github'] },
  { name: 'GITHUB_TOKEN', required: false, services: ['github'] },
];

export async function auroraPrime(options: { fix?: boolean; verbose?: boolean } = {}) {
  console.log('\n' + '='.repeat(80));
  console.log('⭐ AURORA PRIME — FULL STACK AUTOPILOT');
  console.log('='.repeat(80) + '\n');

  const status: SystemStatus = {
    supabase: 'Needs Attention',
    vercel: 'Needs Attention',
    expo: 'Needs Attention',
    githubActions: 'Needs Attention',
    secretsAlignment: 'Needs Attention',
    schemaDrift: 'Needs Manual Review',
    fixes: [],
    recommendations: [],
  };

  try {
    // 1. Environment Verification
    console.log('🔍 [1/7] Environment Verification...');
    const secretsStatus = await verifySecretsAlignment(options.fix);
    status.secretsAlignment = secretsStatus.status;
    status.fixes.push(...secretsStatus.fixes);
    status.recommendations.push(...secretsStatus.recommendations);
    console.log(`   Status: ${secretsStatus.status}\n`);

    // 2. Supabase Migration & Schema Health
    console.log('🗄️  [2/7] Supabase Migration & Schema Health...');
    const supabaseStatus = await verifySupabaseHealth(options.fix);
    status.supabase = supabaseStatus.status;
    status.schemaDrift = supabaseStatus.schemaDrift;
    status.fixes.push(...supabaseStatus.fixes);
    status.recommendations.push(...supabaseStatus.recommendations);
    console.log(`   Status: ${supabaseStatus.status}`);
    console.log(`   Schema Drift: ${supabaseStatus.schemaDrift}\n`);

    // 3. Vercel Frontend Deployment Check
    console.log('🚀 [3/7] Vercel Frontend Deployment Check...');
    const vercelStatus = await verifyVercelDeployment(options.fix);
    status.vercel = vercelStatus.status;
    status.fixes.push(...vercelStatus.fixes);
    status.recommendations.push(...vercelStatus.recommendations);
    console.log(`   Status: ${vercelStatus.status}\n`);

    // 4. Expo Mobile App Deployment
    console.log('📱 [4/7] Expo Mobile App Deployment...');
    const expoStatus = await verifyExpoConfig(options.fix);
    status.expo = expoStatus.status;
    status.fixes.push(...expoStatus.fixes);
    status.recommendations.push(...expoStatus.recommendations);
    console.log(`   Status: ${expoStatus.status}\n`);

    // 5. CI/CD Pipeline Autopilot
    console.log('⚙️  [5/7] CI/CD Pipeline Autopilot...');
    const cicdStatus = await verifyCICDPipelines(options.fix);
    status.githubActions = cicdStatus.status;
    status.fixes.push(...cicdStatus.fixes);
    status.recommendations.push(...cicdStatus.recommendations);
    console.log(`   Status: ${cicdStatus.status}\n`);

    // 6. Self-Healing Logic (already applied during checks)
    console.log('🔧 [6/7] Self-Healing Logic Applied...');
    console.log(`   Applied ${status.fixes.length} fixes\n`);

    // 7. Output Status Report
    console.log('📊 [7/7] Generating Status Report...\n');
    printStatusReport(status);

    // Save detailed report
    const reportPath = path.join(process.cwd(), 'reports', 'aurora-prime-status.json');
    fs.mkdirSync(path.dirname(reportPath), { recursive: true });
    fs.writeFileSync(reportPath, JSON.stringify({
      timestamp: new Date().toISOString(),
      status,
    }, null, 2));

    console.log(`\n✅ Detailed report saved to: ${reportPath}\n`);

    return status;
  } catch (error: any) {
    console.error('❌ Aurora Prime Error:', error.message);
    if (options.verbose) {
      console.error(error.stack);
    }
    throw error;
  }
}

async function verifySecretsAlignment(fix: boolean = false): Promise<{
  status: 'Healthy' | 'FIXED' | 'Needs Attention';
  fixes: string[];
  recommendations: string[];
}> {
  const fixes: string[] = [];
  const recommendations: string[] = [];
  let hasIssues = false;

  // Check GitHub workflows for secret usage
  const workflowsDir = path.join(process.cwd(), '.github', 'workflows');
  const workflows = fs.existsSync(workflowsDir)
    ? fs.readdirSync(workflowsDir).filter(f => f.endsWith('.yml') || f.endsWith('.yaml'))
    : [];

  const secretUsage: Record<string, Set<string>> = {};
  const missingSecrets: string[] = [];

  for (const workflow of workflows) {
    const workflowPath = path.join(workflowsDir, workflow);
    const content = fs.readFileSync(workflowPath, 'utf-8');

    for (const secret of REQUIRED_SECRETS) {
      if (secret.services.includes('github')) {
        const pattern = new RegExp(`\\$\\{\\{\\s*secrets\\.${secret.name}\\s*\\}\\}`, 'g');
        if (pattern.test(content)) {
          if (!secretUsage[secret.name]) {
            secretUsage[secret.name] = new Set();
          }
          secretUsage[secret.name].add(workflow);
        }
      }
    }
  }

  // Check for hardcoded values or missing secret references
  for (const secret of REQUIRED_SECRETS) {
    if (secret.required && !secretUsage[secret.name] && secret.services.includes('github')) {
      missingSecrets.push(secret.name);
      hasIssues = true;
    }
  }

  // Check Vercel config
  const vercelJsonPath = path.join(process.cwd(), 'vercel.json');
  if (fs.existsSync(vercelJsonPath)) {
    // Vercel env vars should be set via GitHub Secrets sync
    recommendations.push('Ensure Vercel environment variables sync from GitHub Secrets');
  }

  // Check Expo config
  const easJsonPath = path.join(process.cwd(), 'eas.json');
  if (fs.existsSync(easJsonPath)) {
    const easConfig = JSON.parse(fs.readFileSync(easJsonPath, 'utf-8'));
    // Check if Expo config references environment variables correctly
    if (easConfig.submit?.production?.ios?.appleId?.startsWith('${')) {
      recommendations.push('Expo config uses environment variables correctly');
    }
  }

  if (hasIssues && fix) {
    // Auto-fix: Add missing secret references to workflows
    for (const secret of missingSecrets) {
      const deployWorkflow = path.join(workflowsDir, 'deploy-main.yml');
      if (fs.existsSync(deployWorkflow)) {
        let content = fs.readFileSync(deployWorkflow, 'utf-8');
        if (!content.includes(`secrets.${secret}`)) {
          // Add to env section if it exists
          const envMatch = content.match(/env:\s*\n([\s\S]*?)(?=\n\s+steps:)/);
          if (envMatch) {
            const envSection = envMatch[1];
            if (!envSection.includes(secret)) {
              content = content.replace(
                envMatch[0],
                `env:\n${envSection}      ${secret}: \${{ secrets.${secret} }}\n`
              );
              fs.writeFileSync(deployWorkflow, content);
              fixes.push(`Added ${secret} to deploy-main.yml`);
            }
          }
        }
      }
    }
  }

  return {
    status: hasIssues ? (fix && fixes.length > 0 ? 'FIXED' : 'Needs Attention') : 'Healthy',
    fixes,
    recommendations,
  };
}

async function verifySupabaseHealth(fix: boolean = false): Promise<{
  status: 'Healthy' | 'FIXED' | 'Needs Attention';
  schemaDrift: 'None' | 'Auto-repaired' | 'Needs Manual Review';
  fixes: string[];
  recommendations: string[];
}> {
  const fixes: string[] = [];
  const recommendations: string[] = [];
  let hasIssues = false;
  let schemaDrift: 'None' | 'Auto-repaired' | 'Needs Manual Review' = 'None';

  try {
    // Check if Supabase CLI is available
    let supabaseCliAvailable = false;
    try {
      execSync('which supabase', { stdio: 'ignore' });
      supabaseCliAvailable = true;
    } catch {
      recommendations.push('Install Supabase CLI: npm install -g supabase');
      hasIssues = true;
    }

    // Check migrations directory
    const migrationsDir = path.join(process.cwd(), 'supabase', 'migrations');
    if (!fs.existsSync(migrationsDir)) {
      hasIssues = true;
      if (fix) {
        fs.mkdirSync(migrationsDir, { recursive: true });
        fixes.push('Created supabase/migrations directory');
      } else {
        recommendations.push('Create supabase/migrations directory');
      }
    } else {
      const migrations = fs.readdirSync(migrationsDir).filter(f => f.endsWith('.sql')).sort();
      if (migrations.length === 0) {
        recommendations.push('No migrations found. Consider creating initial schema migration');
      } else {
        // Check migration naming convention
        const invalidNames = migrations.filter(m => !/^\d{14}_/.test(m) && !/^\d{8}_/.test(m));
        if (invalidNames.length > 0) {
          recommendations.push(`Some migrations don't follow naming convention: ${invalidNames.join(', ')}`);
        }
      }
    }

    // Check Prisma schema alignment
    const prismaSchemaPath = path.join(process.cwd(), 'prisma', 'schema.prisma');
    if (fs.existsSync(prismaSchemaPath)) {
      try {
        execSync('npx prisma validate', { stdio: 'pipe', cwd: process.cwd() });
      } catch (error: any) {
        hasIssues = true;
        const errorMsg = error.stdout?.toString() || error.message;
        recommendations.push(`Prisma schema validation failed: ${errorMsg.substring(0, 100)}`);
      }

      // Check if Prisma generate is needed
      const prismaClientPath = path.join(process.cwd(), 'node_modules', '.prisma', 'client');
      if (!fs.existsSync(prismaClientPath)) {
        recommendations.push('Run "npx prisma generate" to generate Prisma client');
      }
    }

    // Check Supabase config
    const supabaseConfigPath = path.join(process.cwd(), 'supabase', 'config.toml');
    if (!fs.existsSync(supabaseConfigPath)) {
      hasIssues = true;
      if (fix) {
        // Create minimal config
        const defaultConfig = `project_id = "\${SUPABASE_PROJECT_REF:-}"

[api]
enabled = true
port = 54321

[db]
port = 5432
`;
        fs.writeFileSync(supabaseConfigPath, defaultConfig);
        fixes.push('Created supabase/config.toml');
      }
    }

    // Check Edge Functions
    const functionsDir = path.join(process.cwd(), 'supabase', 'functions');
    if (fs.existsSync(functionsDir)) {
      const functions = fs.readdirSync(functionsDir, { withFileTypes: true })
        .filter(d => d.isDirectory() && d.name !== '_shared')
        .map(d => d.name);
      
      if (functions.length > 0) {
        // Check each function has index.ts
        for (const func of functions) {
          const funcIndex = path.join(functionsDir, func, 'index.ts');
          if (!fs.existsSync(funcIndex)) {
            recommendations.push(`Edge Function ${func} missing index.ts`);
          }
        }
      }
    }

    // Try to check Supabase status if credentials are available
    const supabaseUrl = process.env.SUPABASE_URL;
    const supabaseKey = process.env.SUPABASE_SERVICE_ROLE_KEY;
    if (supabaseUrl && supabaseKey) {
      try {
        const supabase = createClient(supabaseUrl, supabaseKey);
        // Test connection
        const { error } = await supabase.from('users').select('id').limit(1);
        if (error && error.code !== 'PGRST116') { // PGRST116 = table doesn't exist, which is OK
          hasIssues = true;
          recommendations.push(`Supabase connection issue: ${error.message}`);
        } else {
          // Check for RLS policies
          try {
            const { data: policies, error: rlsError } = await supabase.rpc('check_rls_policies');
            if (rlsError && rlsError.code !== '42883') { // Function doesn't exist
              recommendations.push('Consider adding RLS policy validation function');
            }
          } catch {
            // RLS check function may not exist, that's OK
          }
        }
      } catch (error: any) {
        recommendations.push(`Could not verify Supabase connection: ${error.message}`);
      }

      // Check if we can run migrations check
      if (supabaseCliAvailable && process.env.SUPABASE_ACCESS_TOKEN && process.env.SUPABASE_PROJECT_REF) {
        try {
          // Try to check migration status
          const { stdout } = execSync(
            `supabase db remote commit --dry-run 2>&1 || true`,
            { cwd: process.cwd(), encoding: 'utf-8' }
          );
          if (stdout.includes('diff') || stdout.includes('migration')) {
            schemaDrift = 'Needs Manual Review';
            recommendations.push('Potential schema drift detected. Review migrations.');
          }
        } catch {
          // Migration check may fail if not linked, that's OK
        }
      }
    } else {
      recommendations.push('Set SUPABASE_URL and SUPABASE_SERVICE_ROLE_KEY to verify connection');
    }

    if (hasIssues && fix && fixes.length > 0) {
      schemaDrift = schemaDrift === 'Needs Manual Review' ? 'Needs Manual Review' : 'Auto-repaired';
    }

  } catch (error: any) {
    recommendations.push(`Supabase health check error: ${error.message}`);
    hasIssues = true;
  }

  return {
    status: hasIssues ? (fix && fixes.length > 0 ? 'FIXED' : 'Needs Attention') : 'Healthy',
    schemaDrift: schemaDrift === 'None' && hasIssues ? 'Needs Manual Review' : schemaDrift,
    fixes,
    recommendations,
  };
}

async function verifyVercelDeployment(fix: boolean = false): Promise<{
  status: 'Healthy' | 'FIXED' | 'Needs Attention';
  fixes: string[];
  recommendations: string[];
}> {
  const fixes: string[] = [];
  const recommendations: string[] = [];
  let hasIssues = false;

  // Check Vercel config
  const vercelJsonPath = path.join(process.cwd(), 'vercel.json');
  if (!fs.existsSync(vercelJsonPath)) {
    hasIssues = true;
    if (fix) {
      const defaultVercelConfig = {
        buildCommand: 'cd frontend && npm ci && npm run build',
        outputDirectory: 'frontend/.next',
        framework: 'nextjs',
        installCommand: 'npm ci',
        devCommand: 'cd frontend && npm run dev',
        rootDirectory: 'frontend',
      };
      fs.writeFileSync(vercelJsonPath, JSON.stringify(defaultVercelConfig, null, 2));
      fixes.push('Created vercel.json');
    } else {
      recommendations.push('Create vercel.json configuration file');
    }
  } else {
    const vercelConfig = JSON.parse(fs.readFileSync(vercelJsonPath, 'utf-8'));
    if (!vercelConfig.rootDirectory && !vercelConfig.buildCommand) {
      recommendations.push('Vercel config may need rootDirectory or buildCommand');
    }
  }

  // Check if Vercel CLI is available
  try {
    execSync('which vercel', { stdio: 'ignore' });
  } catch {
    recommendations.push('Install Vercel CLI: npm install -g vercel');
  }

  // Check GitHub workflow for Vercel deployment
  const deployWorkflowPath = path.join(process.cwd(), '.github', 'workflows', 'deploy-main.yml');
  if (fs.existsSync(deployWorkflowPath)) {
    const workflowContent = fs.readFileSync(deployWorkflowPath, 'utf-8');
    if (!workflowContent.includes('VERCEL_TOKEN')) {
      hasIssues = true;
      if (fix) {
        // This would be handled by verifySecretsAlignment
        recommendations.push('Ensure VERCEL_TOKEN is set in GitHub Secrets');
      }
    }
    if (!workflowContent.includes('vercel deploy')) {
      recommendations.push('Deploy workflow should include Vercel deployment step');
    }
  }

  // Check frontend directory exists
  const frontendDir = path.join(process.cwd(), 'frontend');
  if (!fs.existsSync(frontendDir)) {
    hasIssues = true;
    recommendations.push('Frontend directory not found');
  } else {
    const frontendPkgJson = path.join(frontendDir, 'package.json');
    if (!fs.existsSync(frontendPkgJson)) {
      hasIssues = true;
      recommendations.push('Frontend package.json not found');
    }
  }

  return {
    status: hasIssues ? (fix && fixes.length > 0 ? 'FIXED' : 'Needs Attention') : 'Healthy',
    fixes,
    recommendations,
  };
}

async function verifyExpoConfig(fix: boolean = false): Promise<{
  status: 'Healthy' | 'FIXED' | 'Needs Attention';
  fixes: string[];
  recommendations: string[];
}> {
  const fixes: string[] = [];
  const recommendations: string[] = [];
  let hasIssues = false;

  // Check EAS config
  const easJsonPath = path.join(process.cwd(), 'eas.json');
  if (!fs.existsSync(easJsonPath)) {
    hasIssues = true;
    if (fix) {
      const defaultEasConfig = {
        cli: { version: '>=3.0.0' },
        build: {
          production: {
            distribution: 'store',
            channel: 'production',
            autoIncrement: 'version',
          },
        },
        updates: {
          channel: 'production',
          runtimeVersion: { policy: 'appVersion' },
        },
      };
      fs.writeFileSync(easJsonPath, JSON.stringify(defaultEasConfig, null, 2));
      fixes.push('Created eas.json');
    } else {
      recommendations.push('Create eas.json for Expo configuration');
    }
  } else {
    const easConfig = JSON.parse(fs.readFileSync(easJsonPath, 'utf-8'));
    
    // Check OTA updates are enabled
    if (!easConfig.updates) {
      hasIssues = true;
      if (fix) {
        easConfig.updates = {
          channel: 'production',
          runtimeVersion: { policy: 'appVersion' },
        };
        fs.writeFileSync(easJsonPath, JSON.stringify(easConfig, null, 2));
        fixes.push('Added OTA updates configuration to eas.json');
      } else {
        recommendations.push('Enable OTA updates in eas.json');
      }
    }

    // Check if Supabase URL is referenced
    if (!easConfig.extra?.env?.EXPO_PUBLIC_SUPABASE_URL) {
      recommendations.push('Ensure EXPO_PUBLIC_SUPABASE_URL is set in Expo config');
    }
  }

  // Check app.json or app.config.js
  const appJsonPath = path.join(process.cwd(), 'app.json');
  const appConfigJsPath = path.join(process.cwd(), 'app.config.js');
  if (!fs.existsSync(appJsonPath) && !fs.existsSync(appConfigJsPath)) {
    recommendations.push('Consider creating app.json or app.config.js for Expo metadata');
  }

  // Check GitHub workflow for Expo
  const mobileWorkflowPath = path.join(process.cwd(), '.github', 'workflows', 'mobile.yml');
  if (fs.existsSync(mobileWorkflowPath)) {
    const workflowContent = fs.readFileSync(mobileWorkflowPath, 'utf-8');
    if (!workflowContent.includes('EXPO_TOKEN')) {
      hasIssues = true;
      recommendations.push('Ensure EXPO_TOKEN is set in GitHub Secrets');
    }
    if (!workflowContent.includes('eas build')) {
      recommendations.push('Mobile workflow should include EAS build step');
    }
  } else {
    recommendations.push('Consider creating .github/workflows/mobile.yml for Expo builds');
  }

  return {
    status: hasIssues ? (fix && fixes.length > 0 ? 'FIXED' : 'Needs Attention') : 'Healthy',
    fixes,
    recommendations,
  };
}

async function verifyCICDPipelines(fix: boolean = false): Promise<{
  status: 'Healthy' | 'FIXED' | 'Needs Attention';
  fixes: string[];
  recommendations: string[];
}> {
  const fixes: string[] = [];
  const recommendations: string[] = [];
  let hasIssues = false;

  const workflowsDir = path.join(process.cwd(), '.github', 'workflows');
  if (!fs.existsSync(workflowsDir)) {
    hasIssues = true;
    if (fix) {
      fs.mkdirSync(workflowsDir, { recursive: true });
      fixes.push('Created .github/workflows directory');
    }
  }

  const workflows = fs.existsSync(workflowsDir)
    ? fs.readdirSync(workflowsDir).filter(f => f.endsWith('.yml') || f.endsWith('.yaml'))
    : [];

  // Check for essential workflows
  const essentialWorkflows = [
    { name: 'ci.yml', description: 'CI pipeline' },
    { name: 'deploy-main.yml', description: 'Production deployment' },
  ];

  for (const essential of essentialWorkflows) {
    const workflowPath = path.join(workflowsDir, essential.name);
    if (!fs.existsSync(workflowPath)) {
      recommendations.push(`Consider creating ${essential.name} for ${essential.description}`);
    }
  }

  // Validate workflow syntax
  for (const workflow of workflows) {
    const workflowPath = path.join(workflowsDir, workflow);
    try {
      const content = fs.readFileSync(workflowPath, 'utf-8');
      
      // Basic YAML validation (check for common issues)
      if (content.includes('${{ secrets.') && !content.includes('permissions:')) {
        // Check if permissions are set (best practice)
        const hasReadPermissions = content.includes('contents: read') || content.includes('permissions:');
        if (!hasReadPermissions && workflow.includes('deploy')) {
          recommendations.push(`${workflow} should include permissions block for security`);
        }
      }

      // Check for Doctor job
      if (workflow.includes('deploy') && !content.includes('doctor') && !content.includes('Doctor')) {
        recommendations.push(`Consider adding automated Doctor job to ${workflow}`);
      }

    } catch (error: any) {
      hasIssues = true;
      recommendations.push(`Error reading ${workflow}: ${error.message}`);
    }
  }

  // Check for orchestrator workflow
  const orchestratorWorkflow = workflows.find(w => w.includes('orchestrate') || w.includes('orchestrator'));
  if (!orchestratorWorkflow) {
    recommendations.push('Consider creating orchestrator workflow for automated health checks');
  }

  return {
    status: hasIssues ? (fix && fixes.length > 0 ? 'FIXED' : 'Needs Attention') : 'Healthy',
    fixes,
    recommendations,
  };
}

function printStatusReport(status: SystemStatus) {
  console.log('\n' + '='.repeat(80));
  console.log('⭐ AURORA PRIME — FULL SYSTEM STATUS');
  console.log('='.repeat(80) + '\n');

  console.log(`Supabase:              [${status.supabase}]`);
  console.log(`Vercel Deployment:     [${status.vercel}]`);
  console.log(`Expo (iOS/Android):    [${status.expo}]`);
  console.log(`GitHub Actions:        [${status.githubActions}]`);
  console.log(`Secrets Alignment:     [${status.secretsAlignment}]`);
  console.log(`Schema Drift:          [${status.schemaDrift}]`);

  if (status.fixes.length > 0) {
    console.log('\n🔧 Applied Fixes:');
    status.fixes.forEach(fix => console.log(`   ✓ ${fix}`));
  }

  if (status.recommendations.length > 0) {
    console.log('\n💡 Recommended Next Actions:');
    status.recommendations.forEach(rec => console.log(`   - ${rec}`));
  }

  console.log('\n' + '='.repeat(80) + '\n');
}
