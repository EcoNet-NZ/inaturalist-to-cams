Feature: Processing a new iNaturalist observation populates a new WeedLocation feature correctly

	Rule: WeedLocation feature is created at the correct location
		Example: Correct location is set for new observations
		Given iNaturalist has a new OMB observation at 'latitude': -41.2920665997, 'longitude': 174.7628175
		When we process the observation
		Then a WeedLocations feature is created at geopoint 'x': 19454507.8536978, 'y': -5055517.338865108 in coordinate system EPSG:3857

	Rule: The 'SiteSource' field is set to 'iNaturalist_v2'
		Example: SiteSource is always set
		Given iNaturalist has a new OMB observation
		When we process the observation
		Then the feature has 'SiteSource' set to 'iNaturalist_v2'

	Rule: The Location address field is set to Location details if provided
		Example: Location address is set if provided
		Given iNaturalist has a new OMB observation with 'Location details' set to 'Flat 2, 123C St Andrews Road'
		When we process the observation
		Then the feature has 'LocationInfo' set to 'Flat 2, 123C St Andrews Road'

	Rule: Date first observed is set to the iNaturalist observed on date
		Example: Date first observed is set
		Given iNaturalist has a new OMB observation observed at 2022-12-22T12:43:56+13:00
		When we process the observation
		Then the feature has 'DateDiscovered' set to date '2022-12-22 12:43:56'

	Rule: Effort to control is truncated to the initial digit
		Example: Three person hours
		Given iNaturalist has a new OMB observation with 'Effort to control' set to '3 = Three person hours'
		When we process the observation
		Then the feature has 'Urgency' set to 3