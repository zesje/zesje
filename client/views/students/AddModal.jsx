import React from 'react';

class AddModal extends React.Component {

    state = {
        active: false
    }

    toggleActive = () => {
        this.setState({
            active: !this.state.active
        })
    }

    render() {

        return(
            <div className="panel-block is-hidden-mobile">
                <button className="button is-link is-outlined is-fullwidth" onClick={this.toggleActive}>
                    <span className="icon is-small">
                        <i className="fa fa-user-plus"></i>
                    </span>
                    <span>add students</span>
                </button>
                <div className={"modal" + (this.state.active ? " is-active" : "")}>
                    <div className="modal-background"></div>
                    <div className="modal-card">
                        <header className="modal-card-head">
                            <p className="modal-card-title">
                                <span className="icon is-medium">
                                    <i className="fa fa-user-plus"></i>
                                </span>
                                <span>Add students</span>
                            </p>
                            <button className="delete" aria-label="close" onClick={this.toggleActive} ></button>
                        </header>
                        <section className="modal-card-body">
                            Hoihoi
                        </section>
                        <footer className="modal-card-foot">
                            <button className="button is-success">Add student</button>
                            <button className="button is-success">Upload file</button>
                            <button className="button" onClick={this.toggleActive}>Done</button>
                        </footer>
                    </div>
                </div>
            </div>
        )
    }
}

export default AddModal;

