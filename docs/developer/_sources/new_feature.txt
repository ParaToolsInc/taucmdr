How to Add Support for New TAU Features
=======================================

Step 1: Update the :any:`Target` model
--------------------------------------

If the new feature requres any external software pacakges make sure the
:any:`Target` model has at least one attribute for those packages.

Step 2: Update the :any:`Application` model
-------------------------------------------

If the new feature requres application-side support (e.g. OpenCL support
in TAU should correspond to OpenCL being used in the application) then
make sure :any:`Application` has at least one attribute for the feature.

Step 3: Update the :any:`Measurement` model
-------------------------------------------

If the new feature alters the application profile (likely since why else
would you have it?) then add a new attribute to :any:`Measurement` to 
control if the new feature should be enabled or not.

Step 4: Update the Common Framework
-----------------------------------

With the new feature described in the model, update the Common Framework
modules in :any:`tau.cf` to react to the new model attributes.  For
example, you may need to add new parameters to 
:any:`TauInstallation.__init__` so the installation object can configure
TAU appropriatly and enable support for the new feature.  

