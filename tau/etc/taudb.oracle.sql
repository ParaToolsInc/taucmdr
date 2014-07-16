
CREATE TABLE version (
    version		    VARCHAR2(100)     
)
/

INSERT INTO version values('2.13.7')
/

CREATE TABLE application (
    id                      NUMBER PRIMARY KEY,
    name                    VARCHAR2(4000),
    version		    VARCHAR2(4000),
    description             VARCHAR2(4000), 
    language                VARCHAR2(4000),
    paradigm                VARCHAR2(4000),
    usage_text              VARCHAR2(4000),
    execution_options       VARCHAR2(4000),
    userdata                VARCHAR2(4000)
)
/

CREATE SEQUENCE application_id_seq
 start with 1
 increment by 1
 nomaxvalue
/


create trigger application_id_seq_trigger
 before insert on application
 for each row
 begin
 select application_id_seq.nextval into :new.id from dual;
 end;
/



CREATE TABLE experiment (
    id                      NUMBER PRIMARY KEY,
    application             INT NOT NULL,
    name                    VARCHAR2(4000),
    system_name             VARCHAR2(4000),
    system_machine_type     VARCHAR2(4000),
    system_arch             VARCHAR2(4000),
    system_os               VARCHAR2(4000),
    system_memory_size      VARCHAR2(4000),
    system_processor_amt    VARCHAR2(4000),
    system_l1_cache_size    VARCHAR2(4000),
    system_l2_cache_size    VARCHAR2(4000),
    system_userdata         VARCHAR2(4000),
    compiler_cpp_name       VARCHAR2(4000),
    compiler_cpp_version    VARCHAR2(4000),
    compiler_cc_name        VARCHAR2(4000),
    compiler_cc_version     VARCHAR2(4000),
    compiler_java_dirpath   VARCHAR2(4000),
    compiler_java_version   VARCHAR2(4000),
    compiler_userdata       VARCHAR2(4000),
    configure_prefix        VARCHAR2(4000),
    configure_arch          VARCHAR2(4000),
    configure_cpp           VARCHAR2(4000),
    configure_cc            VARCHAR2(4000),
    configure_jdk           VARCHAR2(4000),
    configure_profile       VARCHAR2(4000),
    configure_userdata      VARCHAR2(4000),
    userdata                VARCHAR2(4000),
    FOREIGN KEY(application) REFERENCES application(id) 
)
/


CREATE SEQUENCE experiment_id_seq
 start with 1
 increment by 1
 nomaxvalue
/

create trigger experiment_id_seq_trigger
 before insert on experiment
 for each row
 begin
 select experiment_id_seq.nextval into :new.id from dual;
 end;
/



CREATE TABLE trial (
    id                      NUMBER NOT NULL PRIMARY KEY,
    name                    VARCHAR2(4000),
    experiment              INT         NOT NULL,
    time                    TIMESTAMP,
    problem_definition      VARCHAR2(4000),
    node_count              INT,
    contexts_per_node       INT,
    threads_per_context     INT,
    userdata                VARCHAR2(4000),
    FOREIGN KEY(experiment) REFERENCES experiment(id)
)
/



CREATE SEQUENCE trial_id_seq
 start with 1
 increment by 1
 nomaxvalue
/


CREATE TRIGGER trial_id_seq_trigger
 before insert on trial
 for each row
 begin
 select trial_id_seq.nextval into :new.id from dual;
 end;
/



CREATE TABLE metric (
    id                      NUMBER      NOT NULL PRIMARY KEY,
    name                    VARCHAR2(4000)        NOT NULL,
    trial                   INT 	NOT NULL,
    FOREIGN KEY(trial) REFERENCES trial(id)
)
/


CREATE SEQUENCE metric_id_seq
 start with 1
 increment by 1
 nomaxvalue
/


CREATE TRIGGER metric_id_seq_trigger
 before insert on metric
 for each row
 begin
 select metric_id_seq.nextval into :new.id from dual;
 end;
/


CREATE TABLE interval_event (
    id                      NUMBER NOT NULL PRIMARY KEY,
    trial                   INT         NOT NULL,
    name                    VARCHAR2(4000)        NOT NULL,
    group_name              VARCHAR2(4000),
    source_file		    VARCHAR2(4000),
    line_number		    INT,
    line_number_end	    INT,
    FOREIGN KEY(trial) REFERENCES trial(id)
)
/

CREATE SEQUENCE interval_event_id_seq
 start with 1
 increment by 1
 nomaxvalue
/


CREATE TRIGGER interval_event_id_seq_trigger
 before insert on interval_event
 for each row
 begin
 select interval_event_id_seq.nextval into :new.id from dual;
 end;
/


CREATE TABLE atomic_event (
    id                      NUMBER      NOT NULL PRIMARY KEY,
    trial                   INT         NOT NULL,
    name                    VARCHAR2(4000)        NOT NULL,
    group_name              VARCHAR2(4000),
    source_file		    VARCHAR2(4000),
    line_number		    INT,
    FOREIGN KEY(trial) REFERENCES trial(id)
)
/

CREATE SEQUENCE atomic_event_id_seq
 start with 1
 increment by 1
 nomaxvalue
/

CREATE TRIGGER atomic_event_id_seq_trigger
 before insert on atomic_event
 for each row
 begin
 select atomic_event_id_seq.nextval into :new.id from dual;
 end;
/


CREATE TABLE interval_location_profile (
    interval_event          INT         NOT NULL,
    node                    INT         NOT NULL,             
    context                 INT         NOT NULL,
    thread                  INT         NOT NULL,
    metric                  INT 	NOT NULL,
    inclusive_percentage    DOUBLE PRECISION,
    inclusive               DOUBLE PRECISION,
    exclusive_percentage    DOUBLE PRECISION,
    excl		    DOUBLE PRECISION,
    call                    DOUBLE PRECISION,
    subroutines             DOUBLE PRECISION,
    inclusive_per_call      DOUBLE PRECISION,
    sum_exclusive_squared   DOUBLE PRECISION,
    FOREIGN KEY(interval_event) REFERENCES interval_event(id),
    FOREIGN KEY(metric) REFERENCES metric(id)
)
/

CREATE TABLE atomic_location_profile (
    atomic_event            INT         NOT NULL,
    node                    INT         NOT NULL,             
    context                 INT         NOT NULL,
    thread                  INT         NOT NULL,
    sample_count            INT,         
    maximum_value           DOUBLE PRECISION,
    minimum_value           DOUBLE PRECISION,
    mean_value              DOUBLE PRECISION,
    standard_deviation	    DOUBLE PRECISION,
    FOREIGN KEY(atomic_event) REFERENCES atomic_event(id)
)
/

CREATE TABLE interval_total_summary (
    interval_event          INT         NOT NULL,
    metric                  INT 	NOT NULL,
    inclusive_percentage    DOUBLE PRECISION,
    inclusive               DOUBLE PRECISION,
    exclusive_percentage    DOUBLE PRECISION,
    excl		    DOUBLE PRECISION,
    call                    DOUBLE PRECISION,
    subroutines             DOUBLE PRECISION,
    inclusive_per_call      DOUBLE PRECISION,
    sum_exclusive_squared   DOUBLE PRECISION,
    FOREIGN KEY(interval_event) REFERENCES interval_event(id),
    FOREIGN KEY(metric) REFERENCES metric(id)
)
/

CREATE TABLE interval_mean_summary (
    interval_event          INT         NOT NULL,
    metric                  INT 	NOT NULL,
    inclusive_percentage    DOUBLE PRECISION,
    inclusive               DOUBLE PRECISION,
    exclusive_percentage    DOUBLE PRECISION,
    excl		    DOUBLE PRECISION,
    call                    DOUBLE PRECISION,
    subroutines             DOUBLE PRECISION,
    inclusive_per_call      DOUBLE PRECISION,
    sum_exclusive_squared   DOUBLE PRECISION,
	FOREIGN KEY(interval_event) REFERENCES interval_event(id),
	FOREIGN KEY(metric) REFERENCES metric(id)
)
/

CREATE TABLE machine_thread_map (
    id                        INT		NOT NULL,
    trial                     INT       NOT NULL,
    node                      INT       NOT NULL,
    context                   INT       NOT NULL,
    thread                    INT       NOT NULL,
    process_id                INT,
    thread_id                 INT,
    cpu_index                 INT,
    operating_system_name     VARCHAR2(4000),
    operating_system_version  VARCHAR2(4000),
    system_nodename           VARCHAR2(4000),
    system_architecthure      VARCHAR2(4000),
    system_num_processors     INT,
    cpu_type                  VARCHAR2(4000),
    cpu_mhz                   VARCHAR2(4000),
    cpu_cache_size            INT,
    cpu_cache_alignment       INT,
    cpu_num_cores             INT,
    FOREIGN KEY(trial) REFERENCES trial(id)
)
/

CREATE SEQUENCE machine_thread_map_id_seq
 start with 1
 increment by 1
 nomaxvalue
/

CREATE TRIGGER mc_thread_map_id_seq_trigger
 before insert on machine_thread_map
 for each row
 begin
 select machine_thread_map_id_seq.nextval into :new.id from dual;
 end;
/

CREATE INDEX experiment_application_index on experiment (application)/
CREATE INDEX trial_experiment_index on trial (experiment)/
CREATE INDEX interval_event_trial_index on interval_event (trial)/
CREATE INDEX i_loc_i_event_metric_index on interval_location_profile (interval_event, metric)/
CREATE INDEX i_total_i_event_metric_index on interval_total_summary (interval_event, metric)/
CREATE INDEX i_mean_i_event_metric_index on interval_mean_summary (interval_event, metric)/
CREATE INDEX i_loc_f_m_n_c_t_index on interval_location_profile (interval_event, metric, node, context, thread)/
CREATE INDEX atomic_event_trial_index on atomic_event(trial);
CREATE INDEX atomic_location_profile_index on atomic_location_profile(atomic_event);

