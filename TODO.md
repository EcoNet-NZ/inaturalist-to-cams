# Pre-beta
- [x] Rework to use pyinaturalist model based code, see https://github.com/pyinat/pyinaturalist/issues/433

- [x] Make logging consistent
- [x] Improve exception handling
- [x] Use Flake8 for code assessment

- [x] Explore credentials
- [x] Set up bot user to run API
- [x] Check codes are used for all list values (like current status)
- [x] Check capitalisation of iNaturalist observation fields
- [x] Check Geoprivacy not set to obscured on import
- [x] Fix up TODOs in code
- [x] Check all datetime records are written to CAMS with correct date/time
- [x] Add check of item id before deleting data
- [x] Print item id

- [x] KS - Define and check standards for naming of CAMS fields
- [x] Set up project on GitHub Econet organisation
- [x] Determine how to handle warnings/errors on GitHub actions
- [x] Create a job summary of observations synchronised on GitHub, see https://docs.github.com/en/actions/using-workflows/workflow-commands-for-github-actions#adding-a-job-summary
- [x] Check parent hierarchy for a taxon match for Banana Passionfruit observations
- [x] Check Apache license conditions
- [x] Add config for Site URL
- [x] Update to Arcgis api 2.1.0 
- [x] Check 504 error and maybe retry - see https://github.com/EcoNet-NZ/inaturalist-to-cams/actions/runs/3891132634/jobs/6640996900
- [x] Consider mapping TreatmentSubstance of None in iNat to null in CAMS
- [x] For truncated String fields, consider making last 3 characters "..."
- [x] Check duplicate YYY-GUID-visits on visits table
- [x] Check use of `weed_visits[0]` in CamsWriter, should it be using most recent row rather than first 
- [x] Consider removing, or hiding from view, iNaturalist id (is the URL sufficient? - no, we need the id)
- [x] Add dependabot check for new versions
- [x] Fix action so it doesn't show "deploying to dev"

- [ ] Update README

- [ ] Review wording of feature files
- [ ] Remove duplication on iNaturalist steps

- [ ] Create project for Ernle Clarke Reserve (tradescantia, ivy, sycamore, aluminium plant, veldt grass, hanging sedge/carex pendula)

# Main schema
- [ ] SiteSource - change to just iNaturalist not iNaturalist2022
- [ ] Visit Table - hide iNaturalist id and url from view

  
# Post-beta
- [ ] Allow for duplicates to be merged 
- [ ] Allow Weed Location to be a polygon rather than point