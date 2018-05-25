import React from 'react';

import * as api from '../../api.jsx'

class FeedbackBlock extends React.Component {

    state = {
        hover: false,
        checked: false
    }
    leave = () => {
        this.setState({
            hover: false
        })
    }
    enter = () => {
        this.setState({
            hover: true
        })
    }

    static getDerivedStateFromProps(nextProps, prevState) {
        return {checked: nextProps.checked}
    }

    toggle = () => {
        if (!this.state.hover) {

            this.setState({
                checked: !this.state.checked
            })

            api.put('solution/' + this.props.examID + '/' + this.props.submissionID + '/' + this.props.problemID, {
                id: this.props.feedback.id
            })
                .then(result => {
                    if (result.state != this.state.checked) {
                        this.setState({
                            checked: result.checked
                        })
                    }
                })

        }
    }


    render() {
        const score = this.props.feedback.score;

        return (
            <a className="panel-block is-active" onClick={this.toggle} >
                <span className="panel-icon">
                    <i className={"fa fa-" + (this.state.checked ? "check-square-o" : "square-o")}></i>
                </span>
                <span style={{ width: '80%' }}>
                    {this.props.feedback.name}
                </span>
                <div className="field is-grouped">
                    <div className="control">
                        <div className="tags has-addons">
                            {score ? <span className="tag is-link">{this.props.feedback.score}</span> : null}
                            <span className={"tag" + (this.state.hover ? " is-white" : "")} 
                                onMouseEnter={this.enter} onMouseLeave={this.leave} onClick={() => console.log('pencil click')}> 
                                <i className="fa fa-pencil"></i>
                            </span>
                        </div>
                    </div>
                </div>
            </a>
        )
    }
}


export default FeedbackBlock;