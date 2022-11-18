import '../css/ProjectListItem.scss';
import React from 'react';
import update from 'immutability-helper';
import TaskList from './TaskList';
import NewTaskPanel from './NewTaskPanel';
import ImportTaskPanel from './ImportTaskPanel';
import ErrorMessage from './ErrorMessage';
import EditProjectDialog from './EditProjectDialog';
import csrf from '../django/csrf';
import HistoryNav from '../classes/HistoryNav';
import PropTypes from 'prop-types';
import ResizeModes from '../classes/ResizeModes';
import exifr from '../vendor/exifr';
import { _, interpolate } from '../classes/gettext';
import $ from 'jquery';

class ProjectListItem extends React.Component {
  static propTypes = {
      history: PropTypes.object.isRequired,
      data: PropTypes.object.isRequired, // project json
      onDelete: PropTypes.func,
      onTaskMoved: PropTypes.func,
      onProjectDuplicated: PropTypes.func
  }

  constructor(props){
    super(props);

    this.historyNav = new HistoryNav(props.history);

    this.state = {
      showTaskList: this.historyNav.isValueInQSList("project_task_open", props.data.id),
      upload: this.getDefaultUploadState(),
      error: "",
      data: props.data,
      refreshing: false,
      importing: false,
      selecting: false,
      buttons: []
    };

    this.toggleTaskList = this.toggleTaskList.bind(this);
    this.closeUploadError = this.closeUploadError.bind(this);
    this.cancelUpload = this.cancelUpload.bind(this);
    this.handleTaskReview = this.handleTaskReview.bind(this);
    this.handleTaskSaved = this.handleTaskSaved.bind(this);
    this.viewMap = this.viewMap.bind(this);
    this.handleDelete = this.handleDelete.bind(this);
    this.handleEditProject = this.handleEditProject.bind(this);
    this.updateProject = this.updateProject.bind(this);
    this.taskDeleted = this.taskDeleted.bind(this);
    this.taskMoved = this.taskMoved.bind(this);
    this.hasPermission = this.hasPermission.bind(this);
  }

  refresh(){
    // Update project information based on server
    this.setState({refreshing: true});

    this.refreshRequest = 
      $.getJSON(`/api/projects/${this.state.data.id}/`)
        .done((json) => {
          this.setState({data: json});
        })
        .fail((_, __, e) => {
          this.setState({error: e.message});
        })
        .always(() => {
          this.setState({refreshing: false});
        });
  }

  componentWillUnmount(){
    if (this.deleteProjectRequest) this.deleteProjectRequest.abort();
    if (this.refreshRequest) this.refreshRequest.abort();
  }

  getDefaultUploadState(){
    return {
      uploading: false,
      editing: false,
      error: "",
      progress: 0,
      files: [],
      totalCount: 0,
      uploadedCount: 0,
      totalBytes: 0,
      totalBytesSent: 0,
      lastUpdated: 0
    };
  }

  resetUploadState(){
    this.setUploadState(this.getDefaultUploadState());
  }

  setUploadState(props){
    this.setState(update(this.state, {
      upload: {
        $merge: props
      }
    }));
  }

  hasPermission(perm){
    return this.state.data.permissions.indexOf(perm) !== -1;
  }

  componentDidMount(){
    PluginsAPI.Dashboard.triggerAddNewTaskButton({projectId: this.state.data.id, onNewTaskAdded: this.newTaskAdded}, (button) => {
        if (!button) return;

        this.setState(update(this.state, {
            buttons: {$push: [button]}
        }));
    });
  }

  uploadCompleted = (files) => {
    /* Uploads completed by uppy, NOTE: task does not exist until saved (start processing pressed) */

    let totalBytes = 0;
    for (let i = 0; i < files.length; i++)
      totalBytes += files[i].size;
    console.log("Upload completed: ", files.length, files, " TotalBytes: " + totalBytes);

    /* Store the files on the upload.files object */
    this.setUploadState({uploading: false, files: files, progress: 100, totalCount: files.length, totalBytes: totalBytes, totalBytesSent: totalBytes});
  }

  newTaskAdded = () => {
    this.setState({importing: false});
    
    if (this.state.showTaskList){
      this.taskList.refresh();
    }else{
      this.setState({showTaskList: true});
    }
    this.resetUploadState();
    this.refresh();
  }

  setRef(prop){
    return (domNode) => {
      if (domNode != null) this[prop] = domNode;
    }
  }

  toggleTaskList(){
    const showTaskList = !this.state.showTaskList;

    this.historyNav.toggleQSListItem("project_task_open", this.state.data.id, showTaskList);
    
    this.setState({
      showTaskList: showTaskList
    });
  }

  closeUploadError(){
    this.setUploadState({error: ""});
  }

  cancelUpload(e){
  }

  taskDeleted(){
    this.refresh();
  }

  taskMoved(task){
    this.refresh();
    if (this.props.onTaskMoved) this.props.onTaskMoved(task);
  }

  handleDelete(){
    return $.ajax({
          url: `/api/projects/${this.state.data.id}/`,
          type: 'DELETE'
        }).done(() => {
          if (this.props.onDelete) this.props.onDelete(this.state.data.id);
        });
  }


  handleTaskReview(){
    this.setState({selecting: false});
  }

  handleTaskSaved(taskInfo){
    /* Task saved - [Start Processing] button pressed
     * Need to get the files from the tusd server
     * either transfer them or have them stored in object storage
     */

    this.setUploadState({uploading: true, editing: false});

    // Create task
    const formData = {
        name: taskInfo.name,
        options: taskInfo.options,
        processing_node:  taskInfo.selectedNode.id,
        auto_processing_node: taskInfo.selectedNode.key == "auto",
        partial: true
    };

    if (taskInfo.resizeMode === ResizeModes.YES){
        formData.resize_to = taskInfo.resizeSize;
    }

    $.ajax({
        url: `/api/projects/${this.state.data.id}/tasks/`,
        contentType: 'application/json',
        data: JSON.stringify(formData),
        dataType: 'json',
        type: 'POST'
      }).done((task) => {
        if (task && task.id){
            //Process all the uploaded files and add them to the database
            this.submitUpload(task);
        }else{
            this.setState({error: interpolate(_('Cannot create new task. Invalid response from server: %(error)s'), { error: JSON.stringify(task) }) });
            this.handleTaskCanceled();
        }
      }).fail(() => {
        this.setState({error: _("Cannot create new task. Please try again later.")});
        this.handleTaskCanceled();
      });
  }

  handleTaskCanceled = () => {
    this.setState({selecting: false});
    this.resetUploadState();
  }

  handleUpload = () => {
    // Not a second click for adding more files?
    if (!this.state.upload.editing){
      this.handleTaskCanceled();
    }

    this.setUploadState({
      editing: true,
    });

    //Re-open uploads box
    this.setState({selecting: true});
  }

  handleEditProject(){
    this.editProjectDialog.show();
  }

  submitUpload(task){
    //Uploading files finished and task submitted/created
    // - send the file url list via /uploaded api endpoint
    // - commit the task, begins processing
    $.ajax({
        url: `/api/projects/${this.state.data.id}/tasks/${task.id}/uploaded/`,
        contentType: 'application/json',
        data: JSON.stringify(this.state.upload.files),
        dataType: 'json',
        type: 'POST'
      }).done(() => {
        //this.refresh();
        console.log("Submitted uploaded file list...");

        //Commit the task
        $.ajax({
            url: `/api/projects/${this.state.data.id}/tasks/${task.id}/commit/`,
            contentType: 'application/json',
            dataType: 'json',
            type: 'POST'
          }).done((task) => {
            if (task && task.id){
                this.newTaskAdded();
            }else{
                this.setUploadState({error: interpolate(_('Cannot create new task. Invalid response from server: %(error)s'), { error: JSON.stringify(task) }) });
            }
          }).fail(() => {
            this.setUploadState({error: _("Cannot create new task. Please try again later.")});
          });
      });
  }

  updateProject(project){
    return $.ajax({
        url: `/api/projects/${this.state.data.id}/edit/`,
        contentType: 'application/json',
        data: JSON.stringify({
          name: project.name,
          description: project.descr,
          permissions: project.permissions
        }),
        dataType: 'json',
        type: 'POST'
      }).done(() => {
        this.refresh();
      });
  }

  viewMap(){
    location.href = `/map/project/${this.state.data.id}/`;
  }

  handleImportTask = () => {
    this.setState({importing: true});
  }

  handleCancelImportTask = () => {
    this.setState({importing: false});
  }

  handleTaskTitleHint = () => {

      return new Promise((resolve, reject) => {

          // Find first image in list
          let f = null;
          for (let i = 0; i < this.state.upload.files.length; i++){
            if (this.state.upload.files[i].type.indexOf("image") === 0){
                f = this.state.upload.files[i];
                break;
            }
          }

          if (f === null) {
            //Signal still waiting for valid image upload to generate suggestion
            resolve('');
          } else {

              //if (!f && this.state.upload.files.length > 1){
              if (!f){
                  reject();
                  return;
              }

              //Use URL if provided instead of filename
              if (f["uploadURL"])
                f = f["uploadURL"];
              
              // Parse EXIF
              console.log("EXIF parse: " + f);
              const options = {
                ifd0: false,
                exif: [0x9003], //0x9003 = 'DateTimeOriginal'
                gps: [0x0001, 0x0002, 0x0003, 0x0004],
                interop: false,
                ifd1: false // thumbnail
              };
              console.log("EXIF parse2: " + JSON.stringify(options));
              exifr.parse(f, options).then(gps => {
                let dateTime = gps["36867"];

                // Try to parse the date from EXIF to JS
                const parts = dateTime.split(" ");
                if (parts.length == 2){
                    let [ d, t ] = parts;
                    d = d.replace(/:/g, "-");
                    const tm = Date.parse(`${d} ${t}`);
                    if (!isNaN(tm)){
                        dateTime = new Date(tm).toLocaleDateString();
                    }
                }

                console.log("EXIF parsed: " + JSON.stringify(gps));
                
                // Fallback to file modified date if 
                // no exif info is available
                if (!dateTime) dateTime = f.lastModifiedDate.toLocaleDateString();

                if (!gps.latitude || !gps.longitude){
                    //reject();
                    //Use date/time from exif
                    dateTime = gps[0x9003];
                    if (!dateTime) dateTime = f.lastModifiedDate.toLocaleDateString();
                    resolve(`Unknown Location - ${dateTime}`);
                } else {
                    // Query nominatim OSM
                    $.ajax({
                        url: `https://nominatim.openstreetmap.org/reverse?format=jsonv2&lat=${gps.latitude}&lon=${gps.longitude}`,
                        contentType: 'application/json',
                        type: 'GET'
                    }).done(json => {
                        console.log("EXIF GPS parsed: " + JSON.stringify(json));
                        if (json.name) resolve(`${json.name} - ${dateTime}`);
                        else if (json.display_name) resolve(`${json.display_name} - ${dateTime}`);
                        else if (json.address && json.address.road) resolve(`${json.address.road} - ${dateTime}`);
                        else if (json.address && json.address.village) resolve(`${json.address.village} - ${dateTime}`);
                        else reject(new Error("Invalid json"));
                    }).fail(reject);
                }
              }).catch(reject);
          }
      });
  }

  render() {
    const { refreshing, data } = this.state;
    const numTasks = data.tasks.length;
    const canEdit = this.hasPermission("change");

    return (
      <li className={"project-list-item list-group-item " + (refreshing ? "refreshing" : "")}
         href="javascript:void(0);"
         ref={this.setRef("dropzone")}
         >
        
        {canEdit ? 
            <EditProjectDialog 
            ref={(domNode) => { this.editProjectDialog = domNode; }}
            title={_("Edit Project")}
            saveLabel={_("Save Changes")}
            savingLabel={_("Saving changes...")}
            saveIcon="far fa-edit"
            showDuplicate={true}
            onDuplicated={this.props.onProjectDuplicated}
            projectName={data.name}
            projectDescr={data.description}
            projectId={data.id}
            saveAction={this.updateProject}
            showPermissions={this.hasPermission("change")}
            deleteAction={this.hasPermission("delete") ? this.handleDelete : undefined}
            />
        : ""}

        <div className="row no-margin">
          <ErrorMessage bind={[this, 'error']} />
          <div className="btn-group project-buttons">
            {this.hasPermission("add") ? 
              <div className={"asset-download-buttons btn-group " + (this.state.upload.uploading ? "hide" : "")}>
                <button
                      type="button"
                      className="btn btn-primary btn-sm"
                      onClick={this.handleUpload}
                      ref={this.setRef("uploadButton")}>
                  <i className="glyphicon glyphicon-upload"></i>
                  {_("Upload Data")}
                </button>
                <button type="button" 
                      className="btn btn-default btn-sm"
                      onClick={this.handleImportTask}>
                  <i className="glyphicon glyphicon-import"></i> {_("Import")}
                </button>
                {/* Load the plugin buttons... */}
                {this.state.buttons.map((button, i) => <React.Fragment key={i}>{button}</React.Fragment>)}
              </div>
            : ""}

            <button disabled={this.state.upload.error !== ""} 
                    type="button"
                    className={"btn btn-danger btn-sm " + (!this.state.upload.uploading ? "hide" : "")} 
                    onClick={this.cancelUpload}>
              <i className="glyphicon glyphicon-remove-circle"></i>
              Cancel Upload
            </button> 

            <button type="button" className="btn btn-default btn-sm" onClick={this.viewMap}>
              <i className="fa fa-globe"></i> {_("View Map")}
            </button>
          </div>

          <div className="project-name">
            {data.name}
          </div>
          <div className="project-description">
            {data.description}
          </div>
          <div className="row project-links">
            {numTasks > 0 ? 
              <span>
                <i className='fa fa-tasks'></i>
                 <a href="javascript:void(0);" onClick={this.toggleTaskList}>
                  {interpolate(_("%(count)s Tasks"), { count: numTasks})} <i className={'fa fa-caret-' + (this.state.showTaskList ? 'down' : 'right')}></i>
                </a>
              </span>
              : ""}

            {canEdit ? 
                [<i key="edit-icon" className='far fa-edit'></i>
                ,<a key="edit-text" href="javascript:void(0);" onClick={this.handleEditProject}> {_("Edit")}
                </a>]
            : ""}
          </div>
        </div>
        <i className="drag-drop-icon fa fa-inbox"></i>
        <div className="row">
          {this.state.upload.editing ? 
            <NewTaskPanel
              onReview={this.handleTaskReview}
              onSave={this.handleTaskSaved}
              onCancel={this.handleTaskCanceled}
              suggestedTaskName={this.handleTaskTitleHint}
              filesCount={this.state.upload.totalCount}
              showResize={true}
              getFiles={() => this.state.upload.files }
              onCompleted={this.uploadCompleted}
              selecting={this.state.selecting}
            />
          : ""}

          {this.state.importing ? 
            <ImportTaskPanel
              onImported={this.newTaskAdded}
              onCancel={this.handleCancelImportTask}
              projectId={this.state.data.id}
            />
          : ""}

          {this.state.showTaskList ? 
            <TaskList 
                ref={this.setRef("taskList")} 
                source={`/api/projects/${data.id}/tasks/?ordering=-created_at`}
                onDelete={this.taskDeleted}
                onTaskMoved={this.taskMoved}
                hasPermission={this.hasPermission}
                history={this.props.history}
            /> : ""}

        </div>
      </li>
    );
  }
}

export default ProjectListItem;
