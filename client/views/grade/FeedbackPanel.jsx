import React from 'react';

import * as api from '../../api.jsx'

import FeedbackBlock from './FeedbackBlock.jsx';

class FeedbackPanel extends React.Component {

    state = {
        feedback: [],
        remark: null,
        remarkActive: false
    }

    addRemark = () => {
        this.setState({
            remarkActive: true
        })
    }

    componentDidMount = () => {
        if (this.props.problem) {
            api.get('feedback/' + this.props.problem)
                .then(feedback => {
                    this.setState({
                        feedback: feedback
                    })
                })
        }
    }

    componentWillReceiveProps = (nextProps) => {
        if (this.props.problem !== nextProps.problem) {
            api.get('feedback/' + nextProps.problem)
                .then(feedback => {
                    this.setState({
                        feedback: feedback
                    })
                })
        }
    }

    shouldComponentUpdate = (nextProps, nextState) => {
        if (this.props.problem !== nextProps.problem || this.state.feedback != nextState.feedback || this.state.rem) {
            return true;            
        } else {
            console.log('halting re-render')
            return true;
        }
    }

    render() {

        return (
            <nav className="panel">
                <p className="panel-heading">
                    Feedback
                </p>
                {this.state.feedback.map((feedback, i) =>
                    <FeedbackBlock key={i} index={i} feedback={feedback} checked={false} onClick={this.props.editFeedback} />
                )}
                {this.state.remarkActive ?
                    <div className="panel-block">
                        <textarea className="textarea" rows="2" placeholder="remark" />
                    </div>
                    : null
                }
                <div className="panel-block">
                    <button className="button is-link is-outlined is-fullwidth" onClick={this.props.toggleEdit}>
                        <span className="icon is-small">
                            <i className="fa fa-plus"></i>
                        </span>
                        <span>option</span>
                    </button>
                    <button className="button is-link is-outlined is-fullwidth" onClick={this.addRemark}>
                        <span className="icon is-small">
                            <i className="fa fa-plus"></i>
                        </span>
                        <span>remark</span>
                    </button>
                </div>
            </nav>
        )
    }

}
export default FeedbackPanel;