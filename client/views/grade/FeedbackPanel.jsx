import React from 'react';

import * as api from '../../api.jsx'

import FeedbackBlock from './FeedbackBlock.jsx';

class FeedbackPanel extends React.Component {

    state = {
        remark: null
    }

    render() {

        return (
            <nav className="panel">
                <p className="panel-heading">
                    Feedback
                </p>
                {this.props.problem.feedback.map((feedback, i) =>
                    <FeedbackBlock key={feedback.id} examID={this.props.examID} submissionID={this.props.submissionID} problemID={this.props.problem.id}
                        feedback={feedback} checked={this.props.solution.feedback.includes(feedback.id)} onClick={this.props.editFeedback} />
                )}
                <div className="panel-block">
                    <textarea className="textarea" rows="2" placeholder="remark" />
                </div>
                <div className="panel-block">
                    <button className="button is-link is-outlined is-fullwidth" onClick={this.props.toggleEdit}>
                        <span className="icon is-small">
                            <i className="fa fa-plus"></i>
                        </span>
                        <span>option</span>
                    </button>
                </div>
            </nav>
        )
    }

}
export default FeedbackPanel;