package edu.uoregon.tau.paraprof;


import java.awt.Color;

import edu.uoregon.tau.perfdmf.Function;
import edu.uoregon.tau.perfdmf.Group;
import edu.uoregon.tau.perfdmf.UserEvent;

/**
 * LedgerDataElement
 * This object is holds a group, user event, or function for purposes of the ledger window.
 * This provides the ledger window classes a uniform interface to dealing with these objects.
 * It also holds draw coordinates for mouse events.
 * 
 * <P>CVS $Id: LedgerDataElement.java,v 1.5 2007/05/02 19:45:05 amorris Exp $</P>
 * @author	Alan Morris
 * @version	$Revision: 1.5 $
 * @see		LedgerWindow
 * @see		LedgerWindowPanel
 */
public class LedgerDataElement {
    
    public LedgerDataElement(Function function) {
        this.function = function;
        this.elementType = FUNCTION;
    }
    
    public LedgerDataElement(Group group) {
        this.group = group;
        this.elementType = GROUP;
    }
    
    public LedgerDataElement(UserEvent userEvent) {
        this.userEvent = userEvent;
        this.elementType = USEREVENT;
    }
    
    
    public Function getFunction() {
        return function;
    }
    
    public Group getGroup() {
        return group;
    }
    
    public UserEvent getUserEvent() {
        return userEvent;
    }
    
    public String getName() {
        if (elementType == FUNCTION) {
            return ParaProfUtils.getDisplayName(function);
        } else if (elementType == GROUP) {
            return group.getName();
        } else if (elementType == USEREVENT) {
            return userEvent.getName();
        }
        return null;
    }
    
    
    public boolean isShown(ParaProfTrial ppTrial) {
        if (elementType == FUNCTION) {
            return (ppTrial.displayFunction(function));
        } else if (elementType == GROUP) {
            return true;
        } else if (elementType == USEREVENT) {
            return true;
        }
        return true;
    }
    
    
    public boolean isHighlighted(ParaProfTrial ppTrial) {
        if (elementType == FUNCTION) {
            return (ppTrial.getHighlightedFunction() == function);
        } else if (elementType == GROUP) {
            return (ppTrial.getHighlightedGroup() == group);
        } else if (elementType == USEREVENT) {
            return (ppTrial.getHighlightedUserEvent() == userEvent);
        }
        return false;
    }
    
    public Color getHighlightColor(ColorChooser cc) {
        if (elementType == FUNCTION) {
            return cc.getHighlightColor();
        } else if (elementType == GROUP) {
            return cc.getGroupHighlightColor();
        } else if (elementType == USEREVENT) {
            return cc.getUserEventHighlightColor();
        }
        return Color.black;
    }
    
    public void setDrawCoords(int xBeg, int xEnd, int yBeg, int yEnd) {
        this.xBeg = xBeg;
        this.xEnd = xEnd;
        this.yBeg = yBeg;
        this.yEnd = yEnd;
    }
    
    public int getXBeg() {
        return xBeg;
    }

    public int getXEnd() {
        return xEnd;
    }

    public int getYBeg() {
        return yBeg;
    }

    public int getYEnd() {
        return yEnd;
    }

    public Color getColor() {
        if (elementType == FUNCTION) {
            return function.getColor();
        } else if (elementType == GROUP) {
            return group.getColor();
        } else if (elementType == USEREVENT) {
            return userEvent.getColor();
        }
        return new Color(0,0,0);
    }

    public void setColorFlag(boolean colorFlag) {
        if (elementType == GROUP) {
            group.setColorFlag(colorFlag);
        } else if (elementType == USEREVENT) {
            userEvent.setColorFlag(colorFlag);
        }
    }

    public boolean isColorFlagSet() {
        if (elementType == GROUP) {
            return group.isColorFlagSet();
        } else if (elementType == USEREVENT) {
            return userEvent.isColorFlagSet();
        }
        return false;
    }
    
    public void setSpecificColor(Color color) {
        if (elementType == GROUP) {
            group.setSpecificColor(color);
        } else if (elementType == USEREVENT) {
            userEvent.setSpecificColor(color);
        }
       
    }
    
    private int xBeg;
    private int xEnd;
    private int yBeg;
    private int yEnd;
    
    private Function function;
    private UserEvent userEvent;
    private Group group;
    

    private static final int FUNCTION = 0;
    private static final int GROUP = 1;
    private static final int USEREVENT = 2;
    
    int elementType;
}
