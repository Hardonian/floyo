# GitHub Secrets Verification Checklist

**Generated:** 6/26/2026

## Required Secrets


### 1. VERCEL_TOKEN

- **Required:** ✅ YES
- **Found in Workflows:** ✅ YES
- **Description:** Vercel deployment token for CI/CD
- **How to Get:** Get from https://vercel.com/account/tokens → Create Token
- **Status:** [ ] Not Set | [ ] Set | [ ] Verified

**To Set:**
1. Go to GitHub → Repository → Settings → Secrets and variables → Actions
2. Click "New repository secret"
3. Name: `VERCEL_TOKEN`
4. Value: [Get from instructions above]
5. Click "Add secret"


### 2. VERCEL_ORG_ID

- **Required:** ✅ YES
- **Found in Workflows:** ✅ YES
- **Description:** Vercel organization ID
- **How to Get:** Get from Vercel Dashboard → Organization Settings → General
- **Status:** [ ] Not Set | [ ] Set | [ ] Verified

**To Set:**
1. Go to GitHub → Repository → Settings → Secrets and variables → Actions
2. Click "New repository secret"
3. Name: `VERCEL_ORG_ID`
4. Value: [Get from instructions above]
5. Click "Add secret"


### 3. VERCEL_PROJECT_ID

- **Required:** ✅ YES
- **Found in Workflows:** ✅ YES
- **Description:** Vercel project ID
- **How to Get:** Get from Vercel Dashboard → Project Settings → General
- **Status:** [ ] Not Set | [ ] Set | [ ] Verified

**To Set:**
1. Go to GitHub → Repository → Settings → Secrets and variables → Actions
2. Click "New repository secret"
3. Name: `VERCEL_PROJECT_ID`
4. Value: [Get from instructions above]
5. Click "Add secret"


### 4. SUPABASE_ACCESS_TOKEN

- **Required:** ✅ YES
- **Found in Workflows:** ✅ YES
- **Description:** Supabase access token for migrations
- **How to Get:** Get from https://supabase.com/dashboard/account/tokens → Generate New Token
- **Status:** [ ] Not Set | [ ] Set | [ ] Verified

**To Set:**
1. Go to GitHub → Repository → Settings → Secrets and variables → Actions
2. Click "New repository secret"
3. Name: `SUPABASE_ACCESS_TOKEN`
4. Value: [Get from instructions above]
5. Click "Add secret"


### 5. SUPABASE_PROJECT_REF

- **Required:** ✅ YES
- **Found in Workflows:** ✅ YES
- **Description:** Supabase project reference ID
- **How to Get:** Get from Supabase Dashboard → Settings → General → Reference ID
- **Status:** [ ] Not Set | [ ] Set | [ ] Verified

**To Set:**
1. Go to GitHub → Repository → Settings → Secrets and variables → Actions
2. Click "New repository secret"
3. Name: `SUPABASE_PROJECT_REF`
4. Value: [Get from instructions above]
5. Click "Add secret"



## Verification Steps

1. [ ] Go to GitHub → Repository → Settings → Secrets and variables → Actions
2. [ ] Verify all required secrets are listed (values will be hidden)
3. [ ] For each secret:
   - [ ] Verify name matches exactly (case-sensitive)
   - [ ] Verify value is correct (you can't see it, but you can update it)
   - [ ] Test deployment to ensure secrets work

## Testing Secrets

After setting secrets, test by:
1. Creating a test PR (should trigger preview deployment)
2. Merging to main (should trigger production deployment)
3. Check GitHub Actions logs for any secret-related errors

## Troubleshooting

**If deployment fails:**
- Check GitHub Actions logs for specific error
- Verify secret names match exactly (case-sensitive)
- Verify secret values are correct (re-create if needed)
- Check that workflows reference secrets correctly

**If migrations fail:**
- Verify SUPABASE_ACCESS_TOKEN has correct permissions
- Verify SUPABASE_PROJECT_REF matches your project
- Check Supabase Dashboard → Database → Migrations for errors

---

**Status:** ⚠️ Manual verification required (GitHub doesn't allow programmatic access to secrets)

**Next Steps:**
1. Review this checklist
2. Manually verify secrets in GitHub Settings
3. Test deployments to ensure secrets work
4. Update this checklist with verification status

