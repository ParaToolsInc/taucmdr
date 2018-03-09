CXX=tau mpic++

# IMPORTANT NOTE: The <taudir>/<arch>/bin directory should be in your path.
# Please set TAU_MAKEFILE environment variable to point to your stub Makefile
# that is typically found in <taudir>/<arch>/lib/Makefile.tau-<options> 
# You may also pass parameters to the above script by setting the environment
# variable TAU_OPTIONS. Please see tau_compiler.sh -help for a full listing
# and refer to the README file in this directory for more information. 

serialPi: serialPi.cpp
	$(CXX) $(INCLUDE) -g -O2  serialPi.cpp -o serialPi $(LIB)

clean:
	rm serialPi
