/* William Voorhees
/ Performance Research Lab
/
*/



/*
 * Copyright 2004-2005 Sun Microsystems, Inc.  All Rights Reserved.
 *
 * Redistribution and use in source and binary forms, with or without
 * modification, are permitted provided that the following conditions
 * are met:
 *
 *   - Redistributions of source code must retain the above copyright
 *     notice, this list of conditions and the following disclaimer.
 *
 *   - Redistributions in binary form must reproduce the above copyright
 *     notice, this list of conditions and the following disclaimer in the
 *     documentation and/or other materials provided with the distribution.
 *
 *   - Neither the name of Sun Microsystems nor the names of its
 *     contributors may be used to endorse or promote products derived
 *     from this software without specific prior written permission.
 *
 * THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS "AS
 * IS" AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO,
 * THE IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR
 * PURPOSE ARE DISCLAIMED.  IN NO EVENT SHALL THE COPYRIGHT OWNER OR
 * CONTRIBUTORS BE LIABLE FOR ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL,
 * EXEMPLARY, OR CONSEQUENTIAL DAMAGES (INCLUDING, BUT NOT LIMITED TO,
 * PROCUREMENT OF SUBSTITUTE GOODS OR SERVICES; LOSS OF USE, DATA, OR
 * PROFITS; OR BUSINESS INTERRUPTION) HOWEVER CAUSED AND ON ANY THEORY OF
 * LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY, OR TORT (INCLUDING
 * NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE OF THIS
 * SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.
 */

#include "stdlib.h"

//TAU
#include "Profile/Profiler.h"
#include "Profile/TauInit.h"

//Supporting Libraries
#include <limits.h>
#include <iostream>
using namespace std;

#include "TauJVMTI.h"
#include "JVMTIThreadLayer.h"

extern "C" void Tau_profile_exit_all_threads(void);

#define dprintf if (0) printf
/* ------------------------------------------------------------------- */
/* Some constant maximum sizes */

#define MAX_TOKEN_LENGTH        16
#define MAX_THREAD_NAME_LENGTH  512
#define MAX_METHOD_NAME_LENGTH  1024

/* Some constant names that tie to Java class/method names.
 *    We assume the Java class whose static methods we will be calling
 *    looks like:
 *
 * public class TauJVMTI {
 *     private static int engaged;
 *     private static native void _method_entry(Object thr, int cnum, int mnum);
 *     public static void method_entry(int cnum, int mnum)
 *     {
 *         if ( engaged != 0 ) {
 *             _method_entry(Thread.currentThread(), cnum, mnum);
 *         }
 *     }
 *     private static native void _method_exit(Object thr, int cnum, int mnum);
 *     public static void method_exit(int cnum, int mnum)
 *     {
 *         if ( engaged != 0 ) {
 *             _method_exit(Thread.currentThread(), cnum, mnum);
 *         }
 *     }
 * }
 *
 *    The engaged field allows us to inject all classes (even system classes)
 *    and delay the actual calls to the native code until the VM has reached
 *    a safe time to call native methods (Past the JVMTI VM_START event).
 *
 */

#define TAUJVMTI_class        TauJVMTI          /* Name of class we are using */
#define TAUJVMTI_entry        method_entry    /* Name of java entry method */
#define TAUJVMTI_exit         method_exit     /* Name of java exit method */
#define TAUJVMTI_native_entry _method_entry   /* Name of java entry native */
#define TAUJVMTI_native_exit  _method_exit    /* Name of java exit native */
#define TAUJVMTI_engaged      engaged         /* Name of java static field */

/* C macros to create strings from tokens */
#define _STRING(s) #s
#define STRING(s) _STRING(s)


//Get rid of the nasty globals!
static GlobalAgentData *gdata;

GlobalAgentData * get_global_data(){
  return gdata;
}

/* Enter a critical section by doing a JVMTI Raw Monitor Enter */
static void
enter_critical_section(jvmtiEnv *jvmti)
{
    jvmtiError error;

    error = jvmti->RawMonitorEnter(gdata->lock);
    check_jvmti_error(jvmti, error, "Cannot enter with raw monitor");
}

/* Exit a critical section by doing a JVMTI Raw Monitor Exit */
static void
exit_critical_section(jvmtiEnv *jvmti)
{
    jvmtiError error;

    error = jvmti->RawMonitorExit(gdata->lock);
    check_jvmti_error(jvmti, error, "Cannot exit with raw monitor");
}

/* Create a unique method_id based on method number and class number */
static long
make_unique_method_id(unsigned cnum, unsigned mnum){
  //ANSI spec only says that long => int, so we may run into problems on certian architectures 
  //with really large projects (lots of classes/methods). May be eventually remedied by changes
  //to java_crw_demo.
  if(cnum > ULONG_MAX/2){
    fatal_error("class number is too large for use in method id.\n");
  }
  if(mnum > ULONG_MAX/2){
    fatal_error("method number is too large for use in method id.\n");
  }
  //shift cnum into the top half of the return, and place mnum int he bottom.
  //It's not likely that MSB of cnum is set. Let's set this bit so we will have
  //no collision with CreateTopLevelRoutine().
  return ((unsigned long)cnum << 4*sizeof(unsigned long)) | mnum | 1l<<(sizeof(long)*8 -1);
}

/* Extract method and class number from unique method_id */
static void extract_unique_method_id(long method_id, unsigned * cnum, unsigned * mnum){
  *mnum = (ULONG_MAX >> (sizeof(unsigned long) >> 1)) && method_id;
  *cnum = (ULONG_MAX << (sizeof(unsigned long ) >> 1)) && method_id;
}


/* Get a name for a jthread */
static void
get_thread_name(jvmtiEnv *jvmti, jthread thread, char *tname, int maxlen)
{
    jvmtiThreadInfo info;
    jvmtiError      error;

    /* Make sure the stack variables are garbage free */
    (void)memset(&info,0, sizeof(info));

    /* Assume the name is unknown for now */
    (void)strcpy(tname, "Unknown");

    /* Get the thread information, which includes the name */
    error = jvmti->GetThreadInfo(thread, &info);
    check_jvmti_error(jvmti, error, "Cannot get thread info");

    /* The thread might not have a name, be careful here. */
    if ( info.name != NULL ) {
        int len;

        /* Copy the thread name into tname if it will fit */
        len = (int)strlen(info.name);
        if ( len < maxlen ) {
//            (void)strcpy(tname, info.name);
            sprintf(tname, "THREAD=%s", info.name);
        }

        /* Every string allocated by JVMTI needs to be freed */
        deallocate(jvmti, (void*)info.name);
    }
}

/* Get a name for a jthread */
static void
get_thread_group_name(jvmtiEnv *jvmti, jthread thread, char *gname, int maxlen)
{
    jvmtiThreadGroupInfo group_info;
    jvmtiThreadInfo thread_info;
    jvmtiError      error, error_group;

    /* Make sure the stack variables are garbage free */
    (void)memset(&thread_info,0, sizeof(thread_info));
    (void)memset(&group_info,0, sizeof(group_info));

    /* Assume the name is unknown for now */
    (void)strcpy(gname, "Unknown");

    error = jvmti->GetThreadInfo(thread, &thread_info);
    check_jvmti_error(jvmti, error, "Cannot get thread info");

    /* Get the thread information, which includes the name */
    error_group = jvmti->GetThreadGroupInfo(thread_info.thread_group, &group_info);
    check_jvmti_error(jvmti, error_group, "Cannot get thread group info");

    /* The thread might not have a name, be careful here. */
    if ( group_info.name != NULL ) {
        int len;

        /* Copy the thread name into tname if it will fit */
        len = (int)strlen(group_info.name);
        if ( len < maxlen ) {
//            (void)strcpy(gname, group_info.name);
            sprintf(gname, "%s", group_info.name);
        }

        /* Every string allocated by JVMTI needs to be freed */
        deallocate(jvmti, (void*)group_info.name);
        deallocate(jvmti, (void*)thread_info.name);
    }
}

/* Callback from java_crw_demo() that gives us mnum mappings for TAU */
static void
mnum_callback(const unsigned cnum, const unsigned mnum, const char *class_name, const char *method_name, const char* method_sig){
    char funcname[2048];
    int tid = 0;
    long unique_method_id;
    sprintf(funcname, "%s %s %s", class_name, method_name, method_sig);
    unique_method_id = make_unique_method_id(cnum, mnum);
    //Use of dummy TID is fine, library doesn't use it anyways.
    TAU_MAPPING_CREATE(funcname, " ",
		       unique_method_id , 
		       class_name, tid);
}


/* Wraps agent_util.c's interested function */
static int
instrument_callback(char const * class_name, char const* method_name, char const* method_sig){
  return interested(class_name, method_name, gdata->include, gdata->exclude);
}


/* Java Native Method for entry */
static void
TAUJVMTI_native_entry(JNIEnv *env, jclass klass, jobject thread, jint cnum, jint mnum)
{
    enter_critical_section(gdata->jvmti); {
        /* It's possible we get here right after VmDeath event, be careful */
        if ( !gdata->vm_is_dead ) {
            ClassInfo  *cp;

            if ( cnum >= gdata->ccount ) {
                fatal_error("ERROR: Class number out of range\n");
            }
            cp = gdata->classes + cnum;

            if (gdata->vm_is_initialized) {
	      int tid = JVMTIThreadLayer::GetThreadId(thread);
	      long unique_method_id;

	      unique_method_id = make_unique_method_id(cnum, mnum);

	      //Define a new mapping object TauMethodName
	      TAU_MAPPING_OBJECT(TauMethodName=NULL);
	      //Create a key for this mapping object corrisponding to the method_id
	      TAU_MAPPING_LINK(TauMethodName, unique_method_id);
		
	      TAU_MAPPING_PROFILE_TIMER(TauTimer, TauMethodName, tid);
	      TAU_MAPPING_PROFILE_START(TauTimer,  tid);
            }
        }
    } exit_critical_section(gdata->jvmti);
}

/* Java Native Method for exit */
static void
TAUJVMTI_native_exit(JNIEnv *env, jclass klass, jobject thread, jint cnum, jint mnum)
{
    enter_critical_section(gdata->jvmti); {
        /* It's possible we get here right after VmDeath event, be careful */
        if ( !gdata->vm_is_dead ) {
            ClassInfo  *cp;
	    long unique_method_id;

            if ( cnum >= gdata->ccount ) {
                fatal_error("ERROR: Class number out of range\n");
            }
            cp = gdata->classes + cnum;
            if (gdata->vm_is_initialized) {
		int tid = JVMTIThreadLayer::GetThreadId(thread);
		unique_method_id = make_unique_method_id(cnum, mnum);
		TAU_MAPPING_OBJECT(TauMethodName=NULL);
		TAU_MAPPING_LINK(TauMethodName, unique_method_id);
		TAU_MAPPING_PROFILE_STOP_TIMER(TauMethodName, tid);
            }
        }
    } exit_critical_section(gdata->jvmti);
}

/* Callback for JVMTI_EVENT_VM_START */
static void JNICALL
cbVMStart(jvmtiEnv *jvmti, JNIEnv *env)
{
    enter_critical_section(jvmti); {
        jclass   klass;
        jfieldID field;
        int      rc;

        /* Java Native Methods for class */
        static JNINativeMethod registry[2] = {
            {STRING(TAUJVMTI_native_entry), "(Ljava/lang/Object;II)V",
                (void*)&TAUJVMTI_native_entry},
            {STRING(TAUJVMTI_native_exit),  "(Ljava/lang/Object;II)V",
                (void*)&TAUJVMTI_native_exit}
        };

        /* The VM has started. */
        DEBUGPROFMSG("DEBUGPROF:: VMStart\n");

        /* Register Natives for class whose methods we use */
        klass = env->FindClass(STRING(TAUJVMTI_class));
        if ( klass == NULL ) {
            fatal_error("ERROR: JNI: Cannot find %s with FindClass\n",
                        STRING(TAUJVMTI_class));
        }
        rc = env->RegisterNatives(klass, registry, 2);
        if ( rc != 0 ) {
            fatal_error("ERROR: JNI: Cannot register native methods for %s\n",
                        STRING(TAUJVMTI_class));
        }

        /* Engage calls. */
        field = env->GetStaticFieldID(klass, STRING(TAUJVMTI_engaged), "I");
        if ( field == NULL ) {
            fatal_error("ERROR: JNI: Cannot get field from %s\n",
                        STRING(TAUJVMTI_class));
        }
        env->SetStaticIntField(klass, field, 1);

        /* Indicate VM has started */
        gdata->vm_is_started = JNI_TRUE;

    } exit_critical_section(jvmti);
    DEBUGPROFMSG("DEBUGPROF:: VMStart Finished\n");
}

/* Callback for JVMTI_EVENT_VM_INIT */
static void JNICALL
cbVMInit(jvmtiEnv *jvmti, JNIEnv *env, jthread thread)
{
    enter_critical_section(jvmti); {
        char  tname[MAX_THREAD_NAME_LENGTH];
        static jvmtiEvent events[] =
                { JVMTI_EVENT_THREAD_START, JVMTI_EVENT_THREAD_END };
        int        i;

        /* The VM has started. */
        get_thread_name(jvmti, thread, tname, sizeof(tname));
        DEBUGPROFMSG("DEBUGPROF:: VMInit " <<  tname << endl;);
        dprintf("cbVMInit: tname = %s\n", tname);


        /* The VM is now initialized, at this time we make our requests
         *   for additional events.
         */

        for( i=0; i < (int)(sizeof(events)/sizeof(jvmtiEvent)); i++) {
            jvmtiError error;

            /* Setup event  notification modes */
            error = jvmti->SetEventNotificationMode(JVMTI_ENABLE,
                                  events[i], (jthread)NULL);
            check_jvmti_error(jvmti, error, "Cannot set event notification");
        }
        DEBUGPROFMSG("DEBUGPROF:: VMInit end " << tname << endl;);

	gdata->vm_is_initialized = JNI_TRUE;
    } exit_critical_section(jvmti);
}

/* Callback for JVMTI_EVENT_VM_DEATH */
static void JNICALL
cbVMDeath(jvmtiEnv *jvmti, JNIEnv *env)
{
    enter_critical_section(jvmti); {
        jclass   klass;
        jfieldID field;

        /* The VM has died. */
        DEBUGPROFMSG("VMDeath\n");

        /* Disengage calls in TAUJVMTI_class. */
        klass = env->FindClass(STRING(TAUJVMTI_class));
        if ( klass == NULL ) {
            fatal_error("ERROR: JNI: Cannot find %s with FindClass\n",
                        STRING(TAUJVMTI_class));
        }
        field = env->GetStaticFieldID(klass, STRING(TAUJVMTI_engaged), "I");
        if ( field == NULL ) {
            fatal_error("ERROR: JNI: Cannot get field from %s\n",
                        STRING(TAUJVMTI_class));
        }
        env->SetStaticIntField(klass, field, 0);

        /* The critical section here is important to hold back the VM death
         *    until all other callbacks have completed.
         */

        /* Since this critical section could be holding up other threads
         *   in other event callbacks, we need to indicate that the VM is
         *   dead so that the other callbacks can short circuit their work.
         *   We don't expect any further events after VmDeath but we do need
         *   to be careful that existing threads might be in our own agent
         *   callback code.
         */
        gdata->vm_is_dead = JNI_TRUE;
	TAU_PROFILE_EXIT("OK!");
    } exit_critical_section(jvmti);

}

void CreateTopLevelRoutine(char *name, char *type, char *groupname, int tid) {
  DEBUGPROFMSG("Inside CreateTopLevelRoutine: name = " << name << ", type = " << type  << ", group = " << groupname << ", tid = " << tid  << endl;);
  dprintf("Top level routine: name = %s, type = %s, group = %s\n", name, type, groupname);

  /* Create a top-level routine that is always called. Use the thread name in it */
  TAU_MAPPING_CREATE(name, type, 1, groupname, tid); 
  
  TAU_MAPPING_OBJECT(TauMethodName);
  TAU_MAPPING_LINK(TauMethodName, (long) 1);
  
  TAU_MAPPING_PROFILE_TIMER(TauTimer, TauMethodName, tid);
  TAU_MAPPING_PROFILE_START(TauTimer, tid);
}


/* Callback for JVMTI_EVENT_THREAD_START */
static void JNICALL
cbThreadStart(jvmtiEnv *jvmti, JNIEnv *env, jthread thread)
{
  int * tid;
  dprintf("Thread Start!\n");
  enter_critical_section(jvmti); {
        /* It's possible we get here right after VmDeath event, be careful */
        if ( !gdata->vm_is_dead ) {
            char  tname[MAX_THREAD_NAME_LENGTH];
            char  final_thread_name[MAX_THREAD_NAME_LENGTH];
            char  gname[MAX_THREAD_NAME_LENGTH];

            get_thread_name(jvmti, thread, tname, sizeof(tname));
	    dprintf("Before RegisterThread in cbThreadStart\n");
	    tid = JVMTIThreadLayer::RegisterThread(thread);
            get_thread_group_name(jvmti, thread, gname, sizeof(gname));
	    sprintf(final_thread_name,"%s GROUP=%s",tname, gname);
	    CreateTopLevelRoutine(final_thread_name, " ", gname, *tid); 
        }
    } exit_critical_section(jvmti);
}

/* Callback for JVMTI_EVENT_THREAD_END */
static void JNICALL
cbThreadEnd(jvmtiEnv *jvmti, JNIEnv *env, jthread thread)
{
  dprintf("Thread End!\n");
    enter_critical_section(jvmti); {
        /* It's possible we get here right after VmDeath event, be careful */
        if ( !gdata->vm_is_dead ) {
            char  tname[MAX_THREAD_NAME_LENGTH];

            get_thread_name(jvmti, thread, tname, sizeof(tname));
            DEBUGPROFMSG("ThreadEnd " << tname << endl;);

	    JVMTIThreadLayer::ThreadEnd(thread);
	    //Inform Tau that the thread has ended.
	    TAU_PROFILE_EXIT("END..."); 
        }
    } exit_critical_section(jvmti);
}

/* Callback for JVMTI_EVENT_CLASS_FILE_LOAD_HOOK */
static void JNICALL
cbClassFileLoadHook(jvmtiEnv *jvmti, JNIEnv* env,
                jclass class_being_redefined, jobject loader,
                const char* name, jobject protection_domain,
                jint class_data_len, const unsigned char* class_data,
                jint* new_class_data_len, unsigned char** new_class_data)
{
    enter_critical_section(jvmti); {
        /* It's possible we get here right after VmDeath event, be careful */
        if ( !gdata->vm_is_dead ) {

            const char *classname;

            /* Name could be NULL */
            if ( name == NULL ) {
                classname = java_crw_demo_classname(class_data, class_data_len,
                        NULL);
                if ( classname == NULL ) {
                    fatal_error("ERROR: No classname inside classfile\n");
                }
            } else {
                classname = strdup(name);
                if ( classname == NULL ) {
                    fatal_error("ERROR: Out of malloc memory\n");
                }
            }

            *new_class_data_len = 0;
            *new_class_data     = NULL;

            /* The tracker class itself? */
            if ( interested((char*)classname, "", gdata->include, gdata->exclude)
                  &&  strcmp(classname, STRING(TAUJVMTI_class)) != 0 ) {
                jint           cnum;
                int            system_class;
                unsigned char *new_image;
                long           new_length;
                ClassInfo     *cp;

                /* Get unique number for every class file image loaded */
                cnum = gdata->ccount++;

                /* Save away class information */
                if ( gdata->classes == NULL ) {
                    gdata->classes = (ClassInfo*)malloc(
                                gdata->ccount*sizeof(ClassInfo));
                } else {
                    gdata->classes = (ClassInfo*)
                                realloc((void*)gdata->classes,
                                gdata->ccount*sizeof(ClassInfo));
                }
                if ( gdata->classes == NULL ) {
                    fatal_error("ERROR: Out of malloc memory\n");
                }
                cp           = gdata->classes + cnum;
                cp->name     = (const char *)strdup(classname);
                if ( cp->name == NULL ) {
                    fatal_error("ERROR: Out of malloc memory\n");
                }
                /* Is it a system class? If the class load is before VmStart
                 *   then we will consider it a system class that should
                 *   be treated carefully. (See java_crw_demo)
                 */
                system_class = 0;
                if ( !gdata->vm_is_started ) {
                    system_class = 1;
                }

                new_image = NULL;
                new_length = 0;

                /* Call the class file reader/write demo code */
                java_crw_demo(cnum,
                    classname,
                    class_data,
                    class_data_len,
                    system_class,
                    STRING(TAUJVMTI_class), "L" STRING(TAUJVMTI_class) ";",
                    STRING(TAUJVMTI_entry), "(II)V",
                    STRING(TAUJVMTI_exit), "(II)V",
                    NULL, NULL,
                    NULL, NULL,
                    &new_image,
                    &new_length,
                    NULL,
		    &mnum_callback,
		    &instrument_callback);

                /* If we got back a new class image, return it back as "the"
                 *   new class image. This must be JVMTI Allocate space.
                 */
                if ( new_length > 0 ) {
                    unsigned char *jvmti_space;

                    jvmti_space = (unsigned char *)allocate(jvmti, (jint)new_length);
                    (void)memcpy((void*)jvmti_space, (void*)new_image, (int)new_length);
                    *new_class_data_len = (jint)new_length;
                    *new_class_data     = jvmti_space; /* VM will deallocate */
                }

                /* Always free up the space we get from java_crw_demo() */
                if ( new_image != NULL ) {
                    (void)free((void*)new_image); /* Free malloc() space with free() */
                }
            }
            (void)free((void*)classname);
        }
    } exit_critical_section(jvmti);
}

/* Parse the options for this TauJVMTI agent */
static void
parse_agent_options(char *options)
{
    char token[MAX_TOKEN_LENGTH];
    char const *next;

    gdata->max_count = 10; /* Default max=n */

    /* Parse options and set flags in gdata */
    if ( options==NULL ) {
        return;
    }

    /* Get the first token from the options string. */
    next = get_token(options, ",;=", token, sizeof(token));

    /* While not at the end of the options string, process this option. */
    while ( next != NULL ) {
        if ( strcmp(token,"help")==0 ) {
            stdout_message("The TauJVMTI profiling agent\n");
            stdout_message("\n");
            stdout_message(" java -agent:TauJVMTI[=options] ...\n");
            stdout_message("\n");
	    stdout_message("Options are semicolon separated (make sure to escape it!):\n");
            stdout_message("Within an options the arguments are comma separated:\n");
            stdout_message("\t help\t\t\t Print help information\n");
            stdout_message("\t max=n\t\t Only list top n classes\n");
            stdout_message("\t include=<item>\t\t Only these classes/methods\n");
            stdout_message("\t exclude=<item>\t\t Exclude these classes/methods\n");
            stdout_message("\t node=<NodeID>\t\t Use designated <NodeID> (default=0)\n");
            stdout_message("\n");
            stdout_message("<item>\t Qualified class and/or method names\n");
            stdout_message("\t\t e.g. (*.<init>,Foobar.method,sun.*)\n");
            stdout_message("\n");
            exit(0);
        } else if ( strcmp(token,"include")==0 ) {
            int   used;
            int   maxlen;

            maxlen = MAX_METHOD_NAME_LENGTH;
            if ( gdata->include == NULL ) {
                gdata->include = (char*)calloc(maxlen+1, 1);
                used = 0;
            } else {
                used  = (int)strlen(gdata->include);
                gdata->include[used++] = ',';
                gdata->include[used] = 0;
                gdata->include = (char*)
                             realloc((void*)gdata->include, used+maxlen+1);
            }
            if ( gdata->include == NULL ) {
                fatal_error("ERROR: Out of malloc memory\n");
            }
            /* Add this item to the list */
            next = get_token(next, ";=", gdata->include+used, maxlen);
            /* Check for token scan error */
            if ( next==NULL ) {
                fatal_error("ERROR: include option error\n");
            }
        } else if ( strcmp(token,"exclude")==0 ) {
            int   used;
            int   maxlen;

            maxlen = MAX_METHOD_NAME_LENGTH;
            if ( gdata->exclude == NULL ) {
                gdata->exclude = (char*)calloc(maxlen+1, 1);
                used = 0;
            } else {
                used  = (int)strlen(gdata->exclude);
                gdata->exclude[used++] = ',';
                gdata->exclude[used] = 0;
                gdata->exclude = (char*)
                             realloc((void*)gdata->exclude, used+maxlen+1);
            }
            if ( gdata->exclude == NULL ) {
                fatal_error("ERROR: Out of malloc memory\n");
            }
            /* Add this item to the list */
            next = get_token(next, ";=", gdata->exclude+used, maxlen);
            /* Check for token scan error */
            if ( next==NULL ) {
                fatal_error("ERROR: exclude option error\n");
            }
#ifndef TAU_MPI
	} else if ( strcmp(token,"node")==0 ) {
	    next = get_token(next, ";=", token, sizeof(token));
	    TAU_PROFILE_SET_NODE(atoi(token)); 
#endif
        } else if ( token[0]!=0 ) {
            /* We got a non-empty token and we don't know what it is. */
            fatal_error("ERROR: Unknown option: %s\n", token);
        }
        /* Get the next token (returns NULL if there are no more) */
        next = get_token(next, ",;=", token, sizeof(token));
    }
}

/* Agent_OnLoad: This is called immediately after the shared library is
 *   loaded. This is the first code executed.
 */
JNIEXPORT jint JNICALL
Agent_OnLoad(JavaVM *vm, char *options, void *reserved)
{

    DEBUGPROFMSG("DEBUG_PROF:: Start of Agent_OnLoad\n";);
    static GlobalAgentData data;
    jvmtiEnv              *jvmti;
    jvmtiError             error;
    jint                   res;
    jvmtiCapabilities      capabilities;
    jvmtiEventCallbacks    callbacks;

    /* Setup initial global agent data area
     *   Use of static/extern data should be handled carefully here.
     *   We need to make sure that we are able to cleanup after ourselves
     *     so anything allocated in this library needs to be freed in
     *     the Agent_OnUnload() function.
     */
    (void)memset((void*)&data, 0, sizeof(data));
    gdata = &data;
    dprintf("Agent_OnLoad\n");
    gdata->exclude=strdup("sun,java,com/sun");

// Give TAU some room for its data structures.
#if (!defined(TAU_WINDOWS))

    if (sizeof(void*) < 8) {
      if ((sbrk(1024*1024*4)) == (void *) -1) {
        fprintf(stdout, "TAU>ERROR: sbrk failed\n");
      }
    }
#endif //TAU_WINDOWS


    /* First thing we need to do is get the jvmtiEnv* or JVMTI environment */
    res = vm->GetEnv((void **)&jvmti, JVMTI_VERSION_1);
    if (res != JNI_OK) {
        /* This means that the VM was unable to obtain this version of the
         *   JVMTI interface, this is a fatal error.
         */
        fatal_error("ERROR: Unable to access JVMTI Version 1 (0x%x),"
                " is your JDK a 5.0 or newer version?"
                " JNIEnv's GetEnv() returned %d\n",
               JVMTI_VERSION_1, res);
    }

    /* Here we save the jvmtiEnv* for Agent_OnUnload(). */
    gdata->jvmti = jvmti;

    /*Give our threading layer the handel it needs */
    JVMTIThreadLayer::jvmti = jvmti;

    /*Set up the necessary threading locks now, since they can only
     * be set up during the Onload and Running phases of the JVM
     */
    //    JVMTIThreadLayer::InitializeDBMutexData();
    //    JVMTIThreadLayer::InitializeEnvMutexData();

    Tau_init_initializeTAU();
#ifndef TAU_MPI
    TAU_PROFILE_SET_NODE(0);
#endif /* TAU_MPI */

    /* Register the current thread, since the JVM makes calls with the first thread, before
     * calling cbThreadStart and we need to create the necessary locks and set it's thread ID.
     */
    //JVMTIThreadLayer::RegisterThread();

    /* Parse any options supplied on java command line */
    parse_agent_options(options);

    /* Immediately after getting the jvmtiEnv* we need to ask for the
     *   capabilities this agent will need. In this case we need to make
     *   sure that we can get all class load hooks.
     */
    (void)memset(&capabilities,0, sizeof(capabilities));
    capabilities.can_generate_all_class_hook_events  = 1;
    error = jvmti->AddCapabilities(&capabilities);
    check_jvmti_error(jvmti, error, "Unable to get necessary JVMTI capabilities.");

    /* Next we need to provide the pointers to the callback functions to
     *   to this jvmtiEnv*
     */
    (void)memset(&callbacks,0, sizeof(callbacks));
    /* JVMTI_EVENT_VM_START */
    callbacks.VMStart           = &cbVMStart;
    /* JVMTI_EVENT_VM_INIT */
    callbacks.VMInit            = &cbVMInit;
    /* JVMTI_EVENT_VM_DEATH */
    callbacks.VMDeath           = &cbVMDeath;
    /* JVMTI_EVENT_CLASS_FILE_LOAD_HOOK */
    callbacks.ClassFileLoadHook = &cbClassFileLoadHook;
    /* JVMTI_EVENT_THREAD_START */
    callbacks.ThreadStart       = &cbThreadStart;
    /* JVMTI_EVENT_THREAD_END */
    callbacks.ThreadEnd         = &cbThreadEnd;
    error = jvmti->SetEventCallbacks(&callbacks, (jint)sizeof(callbacks));
    check_jvmti_error(jvmti, error, "Cannot set jvmti callbacks");

    /* At first the only initial events we are interested in are VM
     *   initialization, VM death, and Class File Loads.
     *   Once the VM is initialized we will request more events.
     */
    error = jvmti->SetEventNotificationMode( JVMTI_ENABLE,
                          JVMTI_EVENT_VM_START, (jthread)NULL);
    check_jvmti_error(jvmti, error, "Cannot set event notification");
    error = jvmti->SetEventNotificationMode(JVMTI_ENABLE,
                          JVMTI_EVENT_VM_INIT, (jthread)NULL);
    check_jvmti_error(jvmti, error, "Cannot set event notification");
    error = jvmti->SetEventNotificationMode(JVMTI_ENABLE,
                          JVMTI_EVENT_VM_DEATH, (jthread)NULL);
    check_jvmti_error(jvmti, error, "Cannot set event notification");
    error = jvmti->SetEventNotificationMode(JVMTI_ENABLE,
                          JVMTI_EVENT_CLASS_FILE_LOAD_HOOK, (jthread)NULL);
    check_jvmti_error(jvmti, error, "Cannot set event notification");

    /* Here we create a raw monitor for our use in this agent to
     *   protect critical sections of code.
     */
    error = jvmti->CreateRawMonitor("agent data", &(gdata->lock));
    check_jvmti_error(jvmti, error, "Cannot create raw monitor");

    DEBUGPROFMSG("DEBUG_PROF:: End of Agent_OnLoad\n");

    /* We return JNI_OK to signify success */
    return JNI_OK;
}

/* Agent_OnUnload: This is called immediately before the shared library is
 *   unloaded. This is the last code executed.
 */
JNIEXPORT void JNICALL
Agent_OnUnload(JavaVM *vm)
{
    Tau_profile_exit_all_threads();
      /* Make sure all malloc/calloc/strdup space is freed */
    if ( gdata->include != NULL ) {
        (void)free((void*)gdata->include);
        gdata->include = NULL;
    }
    if ( gdata->exclude != NULL ) {
        (void)free((void*)gdata->exclude);
        gdata->exclude = NULL;
    }
    if ( gdata->classes != NULL ) {
        int cnum;

        for ( cnum = 0 ; cnum < gdata->ccount ; cnum++ ) {
            ClassInfo *cp;

            cp = gdata->classes + cnum;
            (void)free((void*)cp->name);
        }
        (void)free((void*)gdata->classes);
        gdata->classes = NULL;
    }
}
