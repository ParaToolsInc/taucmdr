/*
 *  See TAU License file
 */

/*
 * @author  Wyatt Spear
 * Derived from code by Anthony Chan
 */

package edu.uoregon.tau;

//import java.util.;


import java.util.Date;
import java.util.HashMap;
import java.util.Map;

import base.drawable.*;
//import logformat.trace.*;
import logformat.slog2.*;
import logformat.slog2.output.TreeTrunk;

public class Tau2Slog2
{
    /*static {
        System.loadLibrary( "TraceInput" ); 
    }*/

    private static short    num_children_per_node = 0;
    private static int      leaf_bytesize         = 0;
    private static String   tautrc, tauedf, out_filename;
    private static boolean  enable_endtime_check;
    private static boolean  continue_when_violation;
    private static boolean  papiEnabled;

    @SuppressWarnings("unchecked")
	public static void main( String[] args )
    {
        InputLog							dobj_ins;
        logformat.slog2.output.OutputLog    slog_outs;
        Kind                                next_kind;
        Topology                            topo;
        CategoryMap                         objdefs;   // Drawable def'n
        Map<Topology,Category>                                 shadefs;   // Shadow   def'n
        Category                            objdef;
        LineIDMapList                       lineIDmaps;
        LineIDMap                           lineIDmap;
        Primitive                           prime_obj;
        Composite                           cmplx_obj;
        long                                Nobjs;

        TreeTrunk                           treetrunk;
        double                              prev_dobj_endtime;
        double                              curr_dobj_endtime;
        long                                offended_Nobjs;
        Drawable                            offended_dobj;



        //  Initialize prev_dobj_endtime to avoid complaint by compiler
        prev_dobj_endtime = Double.NEGATIVE_INFINITY;
        offended_Nobjs    = Integer.MIN_VALUE;
        offended_dobj     = null;

        out_filename = null;
        parseCmdLineArgs( args );
        if ( out_filename == null ){
        	int lastP=tautrc.lastIndexOf('.');
        	String outF =tautrc.substring(0, lastP);
        	outF+=".slog2";
        	out_filename=outF;
        	 //out_filename  = TraceName.getDefaultSLOG2Name( tautrc );
        }
           

        objdefs       = new CategoryMap();
        shadefs       = new HashMap<Topology,Category>();
        lineIDmaps    = new LineIDMapList();
        Nobjs         = 0;

        /* */    Date time1 = new Date();
        dobj_ins   = new InputLog( tautrc,tauedf );
        dobj_ins.enablePAPI(papiEnabled);
        slog_outs  = new logformat.slog2.output.OutputLog( out_filename );

        //  Set Tree properties, !optional!
        //  TreeNode's minimum size, without any drawable/shadow, is 38 bytes.
        //  Drawable;s minimum size is 32 bytes, whether it is state/arrow.
        //  Arrow( with 2 integer infovalues ) is 40 bytes long.
        //  So, for 1 state primitive leaf, the size is 38 + 40 = 78 .
        if ( leaf_bytesize > 0 )
            slog_outs.setTreeLeafByteSize( leaf_bytesize );
        if ( num_children_per_node > 0 )
            slog_outs.setNumChildrenPerNode( num_children_per_node );

        treetrunk = new TreeTrunk( slog_outs, shadefs );
        /* */    Date time2 = new Date();
        while ( ( next_kind = dobj_ins.peekNextKind() ) != Kind.EOF ) {
            if ( next_kind == Kind.TOPOLOGY ) {
                topo = dobj_ins.getNextTopology();
                objdef = Category.getShadowCategory( topo );
                objdefs.put( new Integer( objdef.getIndex() ), objdef );
                shadefs.put( topo, objdef );
            }
            else if ( next_kind == Kind.YCOORDMAP ) {
                lineIDmap = new LineIDMap( dobj_ins.getNextYCoordMap() );
                lineIDmaps.add( lineIDmap );
            }
            else if ( next_kind == Kind.CATEGORY ) {
                objdef = dobj_ins.getNextCategory();
                objdefs.put( new Integer(objdef.getIndex() ),objdef );
            }
            else if ( next_kind == Kind.PRIMITIVE ) {
                prime_obj = dobj_ins.getNextPrimitive();
                //System.out.println(objdefs);
                //System.out.println(prime_obj);
                prime_obj.resolveCategory( objdefs );
                // postponed, wait till on-demand decoding of InfoBuffer
                // prime_obj.decodeInfoBuffer();
                Nobjs++;
                // System.out.println( Nobjs + " : " + prime_obj );
                if ( enable_endtime_check ) {
                    if ( ! prime_obj.isTimeOrdered() ) {
                        System.out.println( "**** Primitive Time Error ****" );
                        if ( ! continue_when_violation )
                            System.exit( 1 );
                    }
                    curr_dobj_endtime = prime_obj.getLatestTime();
                    if ( prev_dobj_endtime > curr_dobj_endtime ) {
                        System.err.println( "**** Violation of "
                                          + "Increasing Endtime Order ****\n"
                                          + "\t Offended Drawable -> "
                                          + offended_Nobjs + " : "
                                          + offended_dobj + "\n"
                                          + "\t Offending Primitive -> "
                                          + Nobjs + " : " + prime_obj + "\n"
                                          + "   previous drawable endtime ( "
                                          + prev_dobj_endtime + " ) "
                                          + " > current drawable endtiime ( "
                                          + curr_dobj_endtime + " ) " );
                        if ( ! continue_when_violation )
                            System.exit( 1 );
                    }
                    offended_Nobjs    = Nobjs;
                    offended_dobj     = prime_obj;
                    prev_dobj_endtime = curr_dobj_endtime;
                }
                
//                treetrunk.addDrawable( prime_obj );
                
                try{
                treetrunk.addDrawable( prime_obj );
                }catch(Exception e){
                	e.printStackTrace();
                	
                	System.out.println(prime_obj.toString());
                }
            }
            else if ( next_kind == Kind.COMPOSITE ) {
                cmplx_obj = dobj_ins.getNextComposite();
                cmplx_obj.resolveCategory( objdefs );
                // postponed, wait till on-demand decoding of InfoBuffer
                // cmplx_obj.decodeInfoBuffer();
                Nobjs++;
                // System.out.println( Nobjs + " : " + cmplx_obj );
                if ( enable_endtime_check ) {
                    if ( ! cmplx_obj.isTimeOrdered() ) {
                        System.out.println( "**** Composite Time Error ****" );
                        if ( ! continue_when_violation )
                            System.exit( 1 );
                    }
                    curr_dobj_endtime = cmplx_obj.getLatestTime();
                    if ( prev_dobj_endtime > curr_dobj_endtime ) {
                        System.err.println( "***** Violation of "
                                          + "Increasing Endtime Order! *****\n"
                                          + "\t Offended Drawable -> "
                                          + offended_Nobjs + " : "
                                          + offended_dobj + "\n"
                                          + "\t Offending Composite -> "
                                          + Nobjs + " : " + cmplx_obj + "\n"
                                          + "   previous drawable endtime ( "
                                          + prev_dobj_endtime + " ) "
                                          + " > current drawable endtiime ( "
                                          + curr_dobj_endtime + " ) " );
                        if ( ! continue_when_violation )
                            System.exit( 1 );
                    }
                    offended_Nobjs    = Nobjs;
                    offended_dobj     = cmplx_obj;
                    prev_dobj_endtime = curr_dobj_endtime;
                }
                treetrunk.addDrawable( cmplx_obj );
            }
            else {
                System.err.println( "Tau2Slog2: Unrecognized return "
                                  + "from peekNextKind() = " + next_kind );
            }
        }   // Endof while ( dobj_ins.peekNextKind() )
        //treetrunk.flushToFile();
        try{
        	treetrunk.flushToFile();
            }catch(Exception e){
            	e.printStackTrace();
            	
            
            }

        objdefs.removeUnusedCategories();
        slog_outs.writeCategoryMap( objdefs );

        lineIDmaps.add( treetrunk.getIdentityLineIDMap() );
        slog_outs.writeLineIDMapList( lineIDmaps );

        slog_outs.close();
        dobj_ins.close();

        /* */    Date time3 = new Date();
        System.out.println( "\n" );
        System.out.println( "Number of Drawables = " + Nobjs );

        // System.out.println( "time1 = " + time1 + ", " + time1.getTime() );
        // System.out.println( "time2 = " + time2 + ", " + time2.getTime() );
        // System.out.println( "time3 = " + time3 + ", " + time3.getTime() );
        System.out.println( "timeElapsed between 1 & 2 = "
                          + ( time2.getTime() - time1.getTime() ) + " msec" );
        System.out.println( "timeElapsed between 2 & 3 = "
                          + ( time3.getTime() - time2.getTime() ) + " msec" );
    }

    private static int parseByteSize( String size_str )
    {
        int idxOfKilo = Math.max( size_str.indexOf( 'k' ),
                                  size_str.indexOf( 'K' ) );
        int idxOfMega = Math.max( size_str.indexOf( 'm' ),
                                  size_str.indexOf( 'M' ) );
        if ( idxOfKilo > 0 )
            return Integer.parseInt( size_str.substring( 0, idxOfKilo ) )
                   * 1024;
        else if ( idxOfMega > 0 )
            return Integer.parseInt( size_str.substring( 0, idxOfMega ) )
                   * 1024 * 1024;
        else
            return Integer.parseInt( size_str );
    }

    private static String help_msg = "\nUsage: tau2slog "
                                   + "[options] <tau_trc_file> <tau_edf_file> -o <output.slog2>\n"
                                   + " options: \n"
                                   + "\t [-h|--h|-help|--help]             "
                                   + "\t Display HELP message.\n"
                                   + "\t [-tc]                             "
                                   + "\t Check increasing endtime order,\n"
                                   + "\t                                   "
                                   + "\t exit when 1st violation occurs.\n"
                                   + "\t [-tcc]                            "
                                   + "\t Check increasing endtime order,\n"
                                   + "\t                                   "
                                   + "\t continue when violations occur.\n"
                                   + "\t [-nc number_of_children_per_node] "
                                   + "\t Default value is "
                                   + logformat.slog2.Const.NUM_LEAFS +".\n"
                                   + "\t [-ls max_byte_size_of_leaf_node]  "
                                   + "\t Default value is "
                                   + logformat.slog2.Const.LEAF_BYTESIZE +".\n"
                                   + "\t [-p]                                    Include papi atomic events\n"
                                   + "\t [-o output_filename_with_slog2_suffix]"
                                   + "\n\n"
                                   + " note: \"max_byte_size_of_leaf_node\" "
                                   + "can be specified with suffix "
                                   + "k, K, m or M,\n"
                                   + "       where k or K stands for kilobyte,"
                                   + " m or M stands for megabyte.\n"
                                   + "       e.g. 64k means 65536 bytes.\n"
    + "\n"
    + "Example:\n"
    + "  tau2slog2 tau.trc tau.edf -o tau.slog2\n\n";

    private static void parseCmdLineArgs( String argv[] )
    {
        String        arg_str;
        int           idx;
        StringBuffer  err_msg = new StringBuffer();

        tautrc = null;
        tauedf = null;
        enable_endtime_check     = false;
        continue_when_violation  = false;
        papiEnabled				 = false;

        if ( argv.length == 0 ) {
            System.out.println( help_msg );
            System.out.flush();
            System.exit( 0 );
        }

        idx = 0;
        try {
            while ( idx < argv.length ) {
                if ( argv[ idx ].startsWith( "-" ) ) {
                    if (  argv[ idx ].equals( "-h" ) 
                       || argv[ idx ].equals( "--h" )
                       || argv[ idx ].equals( "-help" )
                       || argv[ idx ].equals( "--help" ) ) {
                        System.out.println( help_msg );
                        System.out.flush();
                        System.exit( 0 );
                    }
                    else if ( argv[ idx ].equals( "-tc" ) ) {
                        enable_endtime_check     = true;
                        continue_when_violation  = false;
                        err_msg.append( "\n endtime_order_check_exit = true" );
                        idx++;
                    }
                    else if ( argv[ idx ].equals( "-tcc" ) ) {
                        enable_endtime_check     = true;
                        continue_when_violation  = true;
                        err_msg.append( "\n endtime_order_check_stay = true" );
                        idx++;
                    }
                    else if ( argv[ idx ].equals( "-nc" ) ) {
                        arg_str = argv[ ++idx ]; 
                        num_children_per_node = Short.parseShort( arg_str );
                        err_msg.append( "\n number_of_children_per_node = "
                                      + arg_str );
                        idx++;
                    }
                    else if ( argv[ idx ].equals( "-ls" ) ) {
                        arg_str = argv[ ++idx ];
                        leaf_bytesize = parseByteSize( arg_str );
                        err_msg.append( "\n max_byte_size_of_leaf_node = "
                                      + arg_str );
                        idx++;
                    }
                    else if ( argv[ idx ].equals( "-o" ) ) {
                        out_filename = argv[ ++idx ].trim();
                        err_msg.append( "\n output_filename = "
                                      + out_filename );
                        idx++;
                        if ( ! out_filename.endsWith( ".slog2" ) )
                            System.err.println( "Warning: The suffix of the "
                                              + "output filename is NOT "
                                              + "\".slog2\"." );
                    }
                    else if ( argv[ idx ].equals( "-p" ) ) {
                    	papiEnabled=true;
                    	err_msg.append( "\n including papi events" );
                    	idx++;
                    }
                    else {
                        System.err.println( "Unrecognized option, "
                                          + argv[ idx ] + ", at "
                                          + indexOrderStr( idx+1 )
                                          + " command line argument" );
                        System.out.flush();
                        System.exit( 1 );
                    }
                }
                else {
                    tautrc   = argv[ idx ];
                    idx++;
                    tauedf = argv[idx];
                    idx++;
                }
            }
        } catch ( ArrayIndexOutOfBoundsException idxerr ) {
            if ( err_msg.length() > 0 )
                System.err.println( err_msg.toString() );
            System.err.println( "Error occurs after option "
                              + argv[ idx-1 ] + ", " + indexOrderStr( idx )
                              + " command line argument." );
            // System.err.println( help_msg );
            idxerr.printStackTrace();
        } catch ( NumberFormatException numerr ) {
            if ( err_msg.length() > 0 )
                System.err.println( err_msg.toString() );
           // String idx_order_str = indexOrderStr( idx );
            System.err.println( "Error occurs after option "
                              + argv[ idx-1 ] + ", " + indexOrderStr( idx )
                              + " command line argument.  It needs a number." );
            // System.err.println( help_msg );
            numerr.printStackTrace();
        }
        
        if ( tautrc == null || tauedf == null ) {
            System.err.println( "The Program needs a TAU trc and edf filename as "
                              + "command line arguments." );
            System.err.println( help_msg );
            System.exit( 1 );
        }
    }

    private static String indexOrderStr( int idx )
    {
        switch (idx) {
            case 1  : return Integer.toString( idx ) + "st";
            case 2  : return Integer.toString( idx ) + "nd";
            case 3  : return Integer.toString( idx ) + "rd";
            default : return Integer.toString( idx ) + "th";
        }
    }
}
