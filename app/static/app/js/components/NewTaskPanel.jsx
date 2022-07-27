import '../css/NewTaskPanel.scss';
import React from 'react';
import EditTaskForm from './EditTaskForm';
import PropTypes from 'prop-types';
import Storage from '../classes/Storage';
import ResizeModes from '../classes/ResizeModes';
import update from 'immutability-helper';
import PluginsAPI from '../classes/plugins/API';
import { _, interpolate } from '../classes/gettext';

// Uppy file uploader components
const Uppy = require('@uppy/core')

import '@uppy/core/dist/style.css'
import '@uppy/dashboard/dist/style.css'

const { Dashboard } = require('@uppy/react');

const GoogleDrive = require('@uppy/google-drive')
const Dropbox = require('@uppy/dropbox')
const OneDrive = require('@uppy/onedrive')
const Webcam = require('@uppy/webcam')
const Tus = require('@uppy/tus')
const Url = require('@uppy/url')
const DropTarget = require('@uppy/drop-target')
const GoldenRetriever = require('@uppy/golden-retriever')
//const XHRUpload = require('@uppy/xhr-upload')

class NewTaskPanel extends React.Component {
  static defaultProps = {
    filesCount: 0,
    showResize: false,
    files: []
  };

  static propTypes = {
      onReview: PropTypes.func.isRequired,
      onSave: PropTypes.func.isRequired,
      onCancel: PropTypes.func,
      filesCount: PropTypes.number,
      files: PropTypes.array,
      showResize: PropTypes.bool,
      getFiles: PropTypes.func,
      suggestedTaskName: PropTypes.oneOfType([PropTypes.string, PropTypes.func]),
      onCompleted: PropTypes.func,
      selecting: PropTypes.bool,
  };

  constructor(props){
    super(props);

    this.state = {
      editTaskFormLoaded: false,
      resizeMode: Storage.getItem('resize_mode') === null ? ResizeModes.YES : ResizeModes.fromString(Storage.getItem('resize_mode')),
      resizeSize: parseInt(Storage.getItem('resize_size')) || 2048,
      items: [], // Coming from plugins,
      taskInfo: {},
      loading: false,
      filesCount: props.filesCount,
      files: props.files
    };

    this.uppy = null;
    let that = this;
    function log(msg) {
      //This doesn't seem to work
      // log to console
      that.uppy.log(msg)
      console.log(msg)
      // show error message to the user
      that.uppy.info(msg, 'error', 500)
    }

    this.uppy = new Uppy({autoProceed: true,
      /*disableThumbnailGenerator: true,
      showSelectedFiles: false,
      closeAfterFinish: true,
      showRemoveButtonAfterComplete: true,*/
      restrictions: {allowedFileTypes : ['image/*', '.txt', '.zip']},
      onBeforeFileAdded: (currentFile, files) => {
        //Filter dotfiles
        if (currentFile.name[0] === '.') {
          log(`Skipping dotfile`)
          return false;
        }

        let ext = currentFile.name.slice(-4)
        if (ext === '.txt' && currentFile.name.indexOf('gcp_list') != 0) {
          log(`Skipping .txt file, only gcp_list.txt permitted`)
          return false;
        }

        //Allow only a single zip to be added at a time
        //(avoids adding zip files in entire folder selections)
        if (ext === '.zip' && Object.keys(files).length > 1) {
          log(`Skipping .zip file in multiple upload, upload archives one at a time`)
          return false;
        }

      }})
      .use(Webcam, {})
      .use(Url, {companionUrl: 'https://companion.uppy.io'})
      .use(GoogleDrive, {companionUrl: 'https://companion.uppy.io'})
      .use(Dropbox, {companionUrl: 'https://companion.uppy.io'})
      .use(OneDrive, {companionUrl: 'https://companion.uppy.io'})
      .use(Tus, {endpoint: location.protocol + '//tusd.' + location.hostname + '/files/'})
      //.use(XHRUpload, {endpoint: `/api/projects/${this.state.data.id}/tasks/${this.state.taskInfo.id}/upload/`})

    this.save = this.save.bind(this);
    this.handleFormTaskLoaded = this.handleFormTaskLoaded.bind(this);
    this.getTaskInfo = this.getTaskInfo.bind(this);
    this.setResizeMode = this.setResizeMode.bind(this);
    this.handleResizeSizeChange = this.handleResizeSizeChange.bind(this);
    this.handleFormChanged = this.handleFormChanged.bind(this);
  }

  componentDidMount(){
    PluginsAPI.Dashboard.triggerAddNewTaskPanelItem({}, (item) => {
        if (!item) return;

        this.setState(update(this.state, {
            items: {$push: [item]}
        }));
    });

    this.uppy.on("files-added", files => {
    });

    this.uppy.on('upload-success', (file, response) => {
      //console.log(file.name, response.uploadURL)
    });

    this.uppy.on('complete', (result) => {
      console.log('successful files:', result.successful.length)
      console.log('failed files:', result.failed.length)

      //Concate files count
      this.setState({filesCount: this.state.filesCount + result.successful.length, files: this.state.files.concat(result.successful)});

      //Callback
      //if (this.props.onCompleted) this.props.onCompleted(result.successful);
      //Pass combined file list
      if (this.props.onCompleted) this.props.onCompleted(this.state.files);

    });
  }

  save(e){

      //[Start Processing] pressed
      this.setState({loading: true});
      e.preventDefault();
      this.taskForm.saveLastPresetToStorage();
      Storage.setItem('resize_size', this.state.resizeSize);
      Storage.setItem('resize_mode', this.state.resizeMode);

      const taskInfo = this.getTaskInfo();
      if (taskInfo.selectedNode.key != "auto"){
        Storage.setItem('last_processing_node', taskInfo.selectedNode.id);
      }else{
        Storage.setItem('last_processing_node', '');
      }

      if (this.props.onSave) this.props.onSave(taskInfo);
  }

  cancel = (e) => {
      if (this.props.onCancel){
        if (window.confirm(_("Are you sure you want to cancel?"))){
          this.props.onCancel();
        }
      }
  }

  getTaskInfo(){
    return Object.assign(this.taskForm.getTaskInfo(), {
      resizeSize: this.state.resizeSize,
      resizeMode: this.state.resizeMode 
    });
  }

  setResizeMode(v){
    return e => {
      this.setState({resizeMode: v});

      setTimeout(() => {
          this.handleFormChanged();
      }, 0);
    }
  }

  handleResizeSizeChange(e){
    // Remove all non-digit characters
    let n = parseInt(e.target.value.replace(/[^\d]*/g, ""));
    if (isNaN(n)) n = "";
    this.setState({resizeSize: n});
    
    setTimeout(() => {
        this.handleFormChanged();
    }, 0);
  }

  handleFormTaskLoaded(){
    this.setState({editTaskFormLoaded: true});
  }

  handleFormChanged(){
    this.setState({taskInfo: this.getTaskInfo()});
  }

  render() {
    return (
      <div className="new-task-panel theme-background-highlight">
        <div className="form-horizontal">
          <div>
            {this.props.selecting ?
              <Dashboard
                uppy={this.uppy}
                doneButtonHandler={this.props.onReview}
                inline="true"
                width="100%"
                //thumbnailWidth="100" //broken
                note="Images files and GCP.txt only"
                plugins={['Webcam', 'Url', 'GoogleDrive', 'Dropbox', 'OneDrive']}
                fileManagerSelectionType='both'
              />
            : ""}

            {this.props.selecting ? <p></p> : ""}

            <p>{interpolate(_("%(count)s files selected. Please check these additional options:"), { count: this.state.filesCount})}</p>

            <EditTaskForm
              selectedNode={Storage.getItem("last_processing_node") || "auto"}
              onFormLoaded={this.handleFormTaskLoaded}
              onFormChanged={this.handleFormChanged}
              suggestedTaskName={this.props.suggestedTaskName}
              ref={(domNode) => { if (domNode) this.taskForm = domNode; }}
            />

            {this.state.editTaskFormLoaded && this.props.showResize ?
              <div>
                <div className="form-group">
                  <label className="col-sm-2 control-label">{_("Resize Images")}</label>
                  <div className="col-sm-10">
                      <div className="btn-group">
                      <button type="button" className="btn btn-default dropdown-toggle" data-toggle="dropdown">
                          {ResizeModes.toHuman(this.state.resizeMode)} <span className="caret"></span>
                      </button>
                      <ul className="dropdown-menu">
                          {ResizeModes.all().map(mode =>
                          <li key={mode}>
                              <a href="javascript:void(0);" 
                                  onClick={this.setResizeMode(mode)}>
                                  <i style={{opacity: this.state.resizeMode === mode ? 1 : 0}} className="fa fa-check"></i> {ResizeModes.toHuman(mode)}</a>
                          </li>
                          )}
                      </ul>
                      </div>
                      <div className={"resize-control " + (this.state.resizeMode === ResizeModes.NO ? "hide" : "")}>
                      <input 
                          type="number" 
                          step="100"
                          className="form-control"
                          onChange={this.handleResizeSizeChange} 
                          value={this.state.resizeSize} 
                      />
                      <span>{_("px")}</span>
                      </div>
                  </div>
                </div>
                {this.state.items.map((Item, i) => <div key={i} className="form-group">
                  <Item taskInfo={this.state.taskInfo}
                        getFiles={() => this.state.files }
                        filesCount={this.state.filesCount}
                      />
                </div>)}
              </div>
            : ""}
          </div>

          {this.state.editTaskFormLoaded ? 
            <div className="form-group">
              <div className="col-sm-offset-2 col-sm-10 text-right">
                {this.props.onCancel !== undefined && <button type="submit" className="btn btn-danger" onClick={this.cancel} style={{marginRight: 4}}><i className="glyphicon glyphicon-remove-circle"></i> {_("Cancel")}</button>}
                {this.state.loading ?
                  <button type="submit" className="btn btn-primary" disabled={true}><i className="fa fa-circle-notch fa-spin fa-fw"></i>{_("Loading…")}</button>
                  :
                  <button type="submit" className="btn btn-primary" onClick={this.save} disabled={this.state.filesCount <= 1}><i className="glyphicon glyphicon-saved"></i>Start Processing</button>
                }
              </div>
            </div>
            : ""}
        </div>
      </div>
    );
  }
}

export default NewTaskPanel;
