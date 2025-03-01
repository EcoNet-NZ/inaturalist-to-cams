# iNaturalist to CAMS User Guide

## Using this guide

You can click on the ![image](https://user-images.githubusercontent.com/144202/233519091-4a0a447e-7605-4b21-9133-57f912939caa.png) icon above to view the Table of Contents and jump to a specific part of this guide.

## Overview

The CAMS weed app enhances our ability to manage weeds across a location by mapping the current status of the weed. The status of controlled weeds is reset annually (currently on 1st October) to `Purple - Please Check`. As people visit the weed during the year, they update the status, typically to `Green - regrowth has not occurred this year` or `Red - growth is occurring, please kill it`. If the weed is controlled, details of the control method are added and the status is changed to `Yellow - growth has been killed this year` or `Orange - dead-headed`. The goal is to recheck all weed locations during the year and update the status, with the end goal of making all the weed locations `Green`.

The weed app shows a map with a marker at each weed location, coloured to show the current known status. Here's an example map:

![map of weed locations coloured by status](https://user-images.githubusercontent.com/144202/234097543-2158539d-a677-4e9a-a4fc-7f58d699386b.png)

Clicking on a weed location shows details about the weed, including a link that takes you to the underlying iNaturalist observation:

![image](https://user-images.githubusercontent.com/144202/234098290-bbbf3ba7-4e1b-40fa-8f56-a3d0f74e6fa9.png)

All observations of the weed are synchronised to CAMS. You can enhance the data in CAMS, and set the weed status/colour, by adding the observation to, or updating it in, the `Weed Management Aotearoa NZ` iNaturalist project. This project contains observation fields that capture additional weed control data for the CAMS application.

This guide assumes you already have an iNaturalist account and would like to add weed management data to your observations.

### Synchroniser

The iNaturalist to CAMS synchroniser creates new records in the CAMS weed app from new iNaturalist observations and updates existing records when the iNaturalist observation is updated. Dependent on the change, it will update the status of each weed and change its colour on the map. It currently runs hourly, so don't expect the observation to be updated in CAMS instantly.

It will synchronise all observations with specific taxa (including descendents) from a particular place. This guide assumes that the taxa and place you are entering are being synchronised. To set up a new synchronisation email office@econet.nz.

## Joining the `Weed Management Aotearoa NZ` project

Before adding an observation to the `Weed Management Aotearoa NZ` project, you'll need to join the project.

Note that this can only be performed on the browser version, not on the mobile app.

Open the [Join Weed Management Aotearoa NZ Project page](https://www.inaturalist.org/projects/weed-management-aotearoa-nz/join), read the project page and select the `Yes, I want to join` button. 

## Adding or updating an observation to the `Weed Management Aotearoa NZ` project

If you're not familiar with adding observations to iNaturalist see [this guide](https://www.inaturalist.org/pages/add-an-observation-nz). 

When creating an observation, please check the location of the observation is accurate, and update it if necessary. This will help us to find the weed in future.

The easiest way to add an observation to the `Weed Management Aotearoa NZ` project is to use the [iNaturalist weed status updater](https://github.com/EcoNet-NZ/inaturalist-weed-status-updater), which is available when you click on the 'Update weed status' button from the CAMS weed pop-up.

### Using the Mobile app

When adding a new observation in iNaturalist, click on the `Add to project(s)` option and select the `Weed Management Aotearoa NZ` project.

When editing one of your observations in iNaturalist, click on the Edit (pencil) icon. (To get to the iNaturalist observation from CAMS, you can click on the weed location dot and then click on the iNaturalist URL.)

Note if someone else created the observation, you'll currently need to use the iNaturalist weed status updater](https://github.com/EcoNet-NZ/inaturalist-weed-status-updater) (or manually using the Browser interface to add it to the `Weed Management Aotearoa NZ` project and/or update the observation fields).

Fill out the fields:

#### Android

<img src="https://user-images.githubusercontent.com/144202/215252973-d7e58184-a85d-4fb3-8f25-2469c897919c.png" alt="Filling in the details on Android and clicking the tick button" width=400/>

#### iPhone

Once you have completed or updated the fields you click the ‘back arrow’ in the top left, which automatically saves your data:

<img src="https://user-images.githubusercontent.com/144202/230739860-cf5b3157-96b9-45f8-b7f3-c397ba99209a.png" alt="Filling in the details on iPhone" width=400/>

### Using a Browser

When adding a new observation in iNaturalist, select the `Projects` option and add the observation to the `Weed Management Aotearoa NZ` project. 

To update an existing observation in iNaturalist, find (and expand if necessary) the `Projects` icon on the right of the screen, click the cog to the right of the `Weed Management Aotearoa NZ` project and select `Fill out project observation fields`:

![image](https://user-images.githubusercontent.com/144202/222978348-8fcc2622-01cc-4e9e-ad72-a88dcfe25192.png)

As you fill out the observation fields, you'll need to press the `Add` button next to each field you wish to set. Failure to do this will mean that the fields are not saved:

<img src="https://user-images.githubusercontent.com/144202/215251731-6f0da4f3-710a-49e7-9b7e-103b67ea0e87.png" alt="Filling in the details and clicking the 'Add' button next to each detail, as well as the 'Add to Project' button" width=400/>

Note that to get to the iNaturalist observation from CAMS, you can click on the weed location dot and then click on the iNaturalist URL.

### Observation Fields

The project contains a number of observation fields. These fields are logically in 3 groups:

1. Weed Details - these should be entered when the weed is first observed, but can be entered or updated later on
2. Weed Control Details - update these fields when you control a weed
3. Status Updates - update these fields when you visit a weed at a later date, but don't control it

Here's details of the fields in each group:

#### Weed Details

The first set of fields help volunteers plan their work and control the weed. It would be great if you could fill these out when you add an OMB observation. They can also be updated on subsequent visits:

|Field name|Description|
|----------|-----------|
|Location details|A short description of the location that is shown on the CAMS map, eg. `under bridge` or `downhill from gate`. The geolocation should guide us to the approximate location|
|Area in square meters|The estimated size of the weed patch|
|Height (m)|The estimated height of the tallest part of the weed, in metres|
|Plant phenology->most common flowering/fruiting reproductive stage|The most common stage of plant growth</dd>
|Site difficulty|The estimated difficulty of accessing the weed. Typically, levels 1-3 might be performed by the general public, level 4 by skilled workers, while level 5 typically requires professionals|
|Effort to control|The estimated time required to control the weed|

#### Weed Control Details

If you have done any control work on the weed, fill in these fields. This may be on the same day the weed was observed, or a later date. If the weed has previously been controlled, update the existing fields to reflect your weed control work.

|Field name|Description|
|----------|-----------|
|Treated|Set to `Yes` if you have controlled the weed, or `Partially` if you've partially controlled it|
|Date controlled|Enter the date the control work was completed|
|How treated|Select the treatment you have used to control the weed|
|Treatment substance|If using herbicide, select the herbicide which you have used|
|Treatment details|Any additional details of how the weed was controlled|
|Date for next visit|Recommended date for a follow-up check or control work|

#### Status Updates

These fields allow you to update the status of an existing observation.
This is typically used when you revisit a weed spot, but don't control it.
You don't need to fill in these fields if it is a new observation or if you have just controlled the weed.

If the status has already been set on the weed, you may need to override the status and/or the date of status update.

|Field name|Description|
|----------|-----------|
|Status update|Whether the weed is currently alive or dead|
|Date of status update|Enter the date the status update was observed|

---

## FAQ

* Why isn't my observation coming through to CAMS?

    Firstly, observations are synchronised hourly. You might need to wait if it's less than an hour since you entered it in iNaturalist.

    If using the mobile app, note that the observations, and updates, are stored locally and uploaded when your phone has a data connection. Sometimes this can get stuck. 

    Try clicking on the home button and then your observations to see if any are currently waiting or being uploaded. 

    Check also that your Settings have "Automatic Upload (Auto Sync)" ticked, or invoke a manual upload. 
    
* How are the status and colour updated in CAMS?

    The changes that are needed to change the colour of the CAMS weed record are:

    | Change in iNaturalist | Status and colour of weed record in CAMS |
    | --------------------- | ---------------------------------------- |
    | New observation | `Red - growth is occurring, please kill it` |
    | `Treated` set to `Yes`, and `Date controlled` set | `Yellow - growth has been killed this year` |
    | `Treated` set to `Partial`, `How Treated` set to `Cut but roots remain` and `Date controlled` set | `Orange - dead-headed` |
    | `Status update` set to `Dead / Not Present` | `Green - regrowth has not occurred this year` |
    | `Status update` set to `Alive / Regrowth` | `Red - growth is occurring, please kill it` |

    As stated at the top of this guide, the status is reset annually currently in October. If the status has already been updated in the 2 months prior, the status will not be reset.
