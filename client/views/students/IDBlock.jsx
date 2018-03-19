import React from 'react';

import * as api from '../../api.jsx';

class IDBlock extends React.Component {

    state = {
        input: "",
        editing: true,
        short: true,
        new: true,
    }

    componentDidMount = () => {
        if (this.props.editStud) {
            this.setState({
                input: this.props.editStud,
                editing: false,
                short: false,
                new: false
            })
        }
    }
    clear = () => {
        this.setState({
            input: "",
            editing: true,
            short: false,
            new: false
        })
    }

    statusIcon = () => {
        if (this.state.editing) {
            return null
        } else {
            const icon = this.state.short ? "exclamation-triangle" : "check";
            return (
                <span className="icon is-small is-right">
                    <i className={"fa fa-" + icon}></i>
                </span>
            )
        }
    }

    helpText = () => {

        if (this.state.editing) {
            return null
        }

        let text;
        let boldText = null;

        if (this.state.short) {
            text = "This entered number is ";
            boldText = "too short"
        } else {
            text = "This student will be "
            boldText = this.state.new ? "added" : "updated"
        }

        return (
            <p className={"help" + this.color()}>{text}<b>{boldText}</b></p>
        )
    }

    color = () => {
        if (this.state.editing) {
            return ""
        } else {
            return this.state.short ? " is-danger" : " is-success"
        }
    }

    changeID = (event) => {
        const patt = new RegExp(/^[1-9]\d*$|^()$/);

        if (patt.test(event.target.value)) {
            this.setState({
                input: event.target.value
            })
        }
    }

    blur = (event) => {

        const id = parseInt(event.target.value);

        if (id >= 1000000) {

            api.get('students/' + id)
                .then(stud => {
                    this.setState({
                        editing: false,
                        short: false,
                        new: false
                    })
                    this.props.setID(id, stud);
                })
                .catch(res => {
                    console.log('If your browser just gave a 404 error, that is normal - do not worry!');
                    this.setState({
                        editing: false,
                        short: false,
                        new: true
                    })
                    this.props.setID(id);
                })
        } else {
            this.setState({
                editing: false,
                short: true,
            })
        }

    }
    focus = () => {
        this.setState({
            editing: true
        })
    }

    render() {

        return (
            <div className="panel-block">
                <div className="field">
                    <label className="label">Student number</label>
                    <div className="control has-icons-left has-icons-right">
                        <input className={"input" + this.color()} type="text" maxLength="7" placeholder="Student number"
                            value={this.state.input} onChange={this.changeID}
                            onBlur={this.blur} onFocus={this.focus} />
                        <span className="icon is-small is-left">
                            <i className="fa fa-user"></i>
                        </span>
                        {this.statusIcon()}
                    </div>
                    {this.helpText()}
                </div>
            </div>
        )
    }


}

export default IDBlock;