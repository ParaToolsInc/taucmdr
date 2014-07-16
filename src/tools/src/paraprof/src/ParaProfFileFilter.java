package edu.uoregon.tau.paraprof;

import java.io.File;

/**
 * A custom FileFilter
 * 
 * <P>CVS $Id: ParaProfFileFilter.java,v 1.3 2007/05/02 19:45:05 amorris Exp $</P>
 * @author  Robert Bell, Alan Morris
 * @version $Revision: 1.3 $
 */

public class ParaProfFileFilter extends javax.swing.filechooser.FileFilter {

    public static String PPK = "ppk";
    public static String TXT = "txt";
    public static String XML = "xml";

    private String extension = null;

    public ParaProfFileFilter(String extension) {
        super();
        this.extension = extension;
    }

    public boolean accept(File f) {
        boolean accept = f.isDirectory(); // must accept directories for JFileChooser to work properly
        if (!accept) {
            String extension = ParaProfFileFilter.getExtension(f);
            if (extension != null) {
                accept = this.extension.equals(extension);
            }
        }
        return accept;
    }

    public String getDescription() {
        if (extension.equals(TXT))
            return "Tab Delimited (*.txt)";
        else if (extension.equals(PPK))
            return "ParaProf Packed Profile (*.ppk)";
        else if (extension.equals(XML))
            return "XML (e.g. TAU Snapshot) (*.xml)";
        else
            return "Unknown Extension (*.*)";
    }

    public String toString() {
        return this.getDescription();
    }

    public String getExtension() {
        return extension;
    }

    public static String getExtension(File f) {
        String s = f.getPath();
        String extension = null;

        int i = s.lastIndexOf('.');
        if (i > 0 && i < s.length() - 1) {
            extension = s.substring(i + 1).toLowerCase();
        }

        return extension;
    }
}
