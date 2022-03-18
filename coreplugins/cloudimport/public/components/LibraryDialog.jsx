import PropTypes from 'prop-types';
import { Component } from "react";
import { Modal, Button } from "react-bootstrap";
import Select from 'react-select';
import "./LibraryDialog.scss";

export default class LibraryDialog extends Component {
	static defaultProps = {
		platform: null,
	};
	static propTypes = {
		onHide: PropTypes.func.isRequired,
		onSubmit: PropTypes.func.isRequired,
		platform: PropTypes.object,
		apiURL: PropTypes.string.isRequired,
  }

  constructor(props){
    super(props);

    this.state = {
				availableFolders: [],
				selectedFolder: null,
				selectedPlatform: null,
				loadingFolders: true,
				error: "",
    };
  }

	componentDidUpdate(){
    if (!this.props.platform) {
      //Re-trigger folder loading on next selection
      //without this we can only load folders for one cloud library
      if (!this.state.loadingFolders) this.setState({loadingFolders: true, selectedFolder: null});
    }

    if (this.props.platform !== null && this.props.platform.type == "library" && this.state.loadingFolders) {
	    $.get(`${this.props.apiURL}/cloudlibrary/${this.props.platform.name}/listfolders` + (this.state.selectedFolder ? this.state.selectedFolder.url : ""))
	    .done(result => {
        let sel = null
	      result.folders.forEach(album => {
	        album.label = album.images_count >= 0 ? `${album.name} (${album.images_count} images)` : `${album.name}`;
	        album.value = album.url;
          //If the currently selected platform is found, re-select now the image count is loaded
          if (this.state.selectedFolder && this.state.selectedFolder.name == album.name && this.state.selectedFolder.images_count == -1)
            sel = album;
	      })
        if (sel != null)
  	      this.setState({selectedPlatform: this.props.platform.name, availableFolders: result.folders, selectedFolder: sel});
        else
  	      this.setState({selectedPlatform: this.props.platform.name, availableFolders: result.folders});
	    })
	    .fail((error) => {
	        this.setState({availableFolders: [], loadingFolders: false, error: "Cannot load folders. Check your internet connection."});
	    })
			.always(() => {
				this.setState({loadingFolders: false});
			});
    }
  }
	
	handleSelectFolder = (e) => {
    //if (this.state.selectedFolder != e)
      this.setState({selectedFolder: e, loadingFolders: true, selectedPlatform: null});
  }

	handleSubmit = e => this.props.onSubmit(this.state.selectedFolder);
	
	render() {
		const {
			onHide,
			platform,
		} = this.props;

		const title = "Import from " + (platform !== null ? platform.name : "Platform");
		const isVisible = platform !== null && platform.type === "library";
		return (
			<Modal className={"folder-select"} onHide={onHide} show={isVisible}>
				<Modal.Header closeButton>
					<Modal.Title>
						{title}
					</Modal.Title>
				</Modal.Header>
				<Modal.Body bsClass="my-modal">
					<p>Import the images from your <a target="_blank" href={platform === null ? "" : platform.server_url}>{platform === null ? "" : platform.name} library</a> into a new task.</p>
					<Select
						className="basic-single"
						classNamePrefix="select"
						isLoading={this.state.loadingFolders}
						isClearable={false}
						isSearchable={true}
						onChange={this.handleSelectFolder}
						options={this.state.availableFolders}
						placeholder={this.state.loadingFolders ? "Fetching folders..." : "Please select a folder"}
						name="options"
					/>
				</Modal.Body>
				<Modal.Footer>
					<Button onClick={onHide}>Close</Button>
					<Button
						bsStyle="primary"
						disabled={this.state.selectedFolder === null || this.state.selectedFolder.images_count < 2}
						onClick={this.handleSubmit}
					>
						<i className={"fa fa-upload"} />
						Import
					</Button>
				</Modal.Footer>
			</Modal>
		);
	}
}
