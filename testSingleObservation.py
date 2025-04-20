
import logging
from inat_to_cams import cams_reader, inaturalist_reader, translator


observation = inaturalist_reader.INatReader().get_single_observation(265642360)
print(observation.location[1])
inat_to_cams_translator = translator.INatToCamsTranslator()
inat_observation = inaturalist_reader.INatReader.flatten(observation)
cams_feature = inat_to_cams_translator.translate(inat_observation)

print(cams_feature)

reader = cams_reader.CamsReader()
inat_id = cams_feature.latest_weed_visit.external_id
existing_feature = reader.read_observation(inat_id)

if existing_feature:
    if existing_feature == cams_feature:

        logging.info('No relevant updates to observation')
    else:
        #weed_geolocation_modified = existing_feature.geolocation != cams_feature.geolocation
        weed_geolocation_modified = (existing_feature.weed_location.iNaturalist_latitude != cams_feature.weed_location.iNaturalist_latitude) or (existing_feature.weed_location.iNaturalist_longitude != cams_feature.weed_location.iNaturalist_longitude)

        weed_location_modified = existing_feature.weed_location != cams_feature.weed_location
        weed_visit_modified = existing_feature.latest_weed_visit != cams_feature.latest_weed_visit
        logging.info('Updating existing feature')
        logging.info(f'Weed geolocation modified? : {weed_geolocation_modified}')
        logging.info(f'Weed location modified? : {weed_location_modified}')
        logging.info(f'Weed visit modified? : {weed_visit_modified}')
else:
    logging.info('Creating new feature')
    weed_geolocation_modified = True
    weed_location_modified = True
    weed_visit_modified = True

# if weed_geolocation_modified or weed_location_modified:
#     # global_id, object_id = self.write_feature(cams_feature, inat_id, existing_feature, dry_run, weed_geolocation_modified)
# else:
#     global_id = existing_feature.weed_location.global_id
#     object_id = existing_feature.weed_location.object_id

# if weed_visit_modified:
#     new_weed_visit_record = self.write_weed_visit(cams_feature, existing_feature, global_id, object_id, dry_run)
# else:
#     new_weed_visit_record = False

# self.write_summary_log(cams_feature, existing_feature, object_id, new_weed_visit_record, weed_geolocation_modified, weed_location_modified, weed_visit_modified)
