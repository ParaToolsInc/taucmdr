package edu.uoregon.tau.paraprof.enums;

import edu.uoregon.tau.paraprof.ParaProfMetric;

/**
 * type-safe enum pattern for unit types
 *    
 * TODO : this class is not implemented yet
 *
 * <P>CVS $Id: UnitType.java,v 1.1 2005/09/26 21:12:46 amorris Exp $</P>
 * @author  Alan Morris
 * @version $Revision: 1.1 $
 */
public abstract class UnitType {

    private final String name;
    private UnitType(String name) { this.name = name; }
    public String toString() { return name; }
    
    public static final UnitType MICROSECONDS = new UnitType("Microseconds") {
        public String getUnitString(double value, ParaProfMetric metric) {
            return "";
        }
    };
    
    
    
    public abstract String getUnitString(double value, ParaProfMetric metric);
    
}
