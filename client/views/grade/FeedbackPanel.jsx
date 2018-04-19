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
                    <FeedbackBlock key={feedback.id} feedback={feedback} checked={false} onClick={this.props.editFeedback} />
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