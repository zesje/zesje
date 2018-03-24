import React from 'react';

import * as api from '../../api.jsx';
import { startOfToday } from 'date-fns';


const BackButton = (props) => (
    <button className="button is-light is-fullwidth" onClick={props.onClick}>
        <span className="icon is-small">
            <i className="fa fa-chevron-left"></i>
        </span>
        <span>back</span>
    </button>
)

const SaveButton = (props) => (
    <button className="button is-link is-fullwidth" disabled={props.disabled} onClick={props.onClick}>
        <span className="icon is-small">
            <i className="fa fa-floppy-o"></i>
        </span>
        <span>{props.exists ? "edit" : "add"}</span>
    </button>
)

class EditPanel extends React.Component {

    state = {
        name: "",
        description: "",
        score: ""
    }

    componentWillMount = () => {
        if (this.props.feedback) {
            const stud = this.props.editStud;
            this.setState({
                id: stud.id,
                firstName: stud.firstName,
                lastName: stud.lastName,
                email: stud.email
            })
        }
    }


    changeName = (event) => {
        this.setState({
            name: event.target.value
        })
    }
    changeDesc = (event) => {
        this.setState({
            description: event.target.value
        })
    }
    changeScore = (event) => {
        this.setState({
            score: event.target.value
        })
    }


    saveFeedback = () => {

        if (this.props.feedback) {

        } else {
            api.post('feedback/' + this.props.problem, this.state)
                .then(feedback => {
                    console.log(feedback)
                    this.props.toggleEdit();
                })
        }
    }


    render() {

        return (
            <nav className="panel">
                <p className="panel-heading">
                    Manage feedback
                </p>

                <div className="panel-block">
                    <div className="field">
                        <label className="label">Name</label>
                        <div className="control has-icons-left">
                            <input className="input" placeholder="Name"
                                value={this.state.name} onChange={this.changeName} />
                            <span className="icon is-small is-left">
                                <i className="fa fa-quote-left"></i>
                            </span>
                        </div>
                    </div>
                </div>

                <div className="panel-block">
                    <div className="field">
                        <label className="label">Description</label>
                        <div className="control has-icons-left">
                            <input className="input" placeholder="Description"
                                value={this.state.description} onChange={this.changeDesc} />
                            <span className="icon is-small is-left">
                                <i className="fa fa-quote-right"></i>
                            </span>
                        </div>

                    </div>
                </div>

                <div className="panel-block">
                    <div className="field">
                        <label className="label">Score</label>
                        <div className="control has-icons-left has-icons-right">
                            <input className="input" placeholder="Score"
                                value={this.state.score} onChange={this.changeScore} />
                            <span className="icon is-small is-left">
                                <i className="fa fa-envelope"></i>
                            </span>
                        </div>
                    </div>
                </div>

                <div className="panel-block">
                    <BackButton onClick={this.props.toggleEdit} />
                    <SaveButton onClick={this.saveFeedback} disabled={!this.state.name} exists={this.props.feedback} />
                </div>
            </nav>
        )
    }
}

export default EditPanel;

