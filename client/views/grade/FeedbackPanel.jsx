import React from 'react';

import * as api from '../../api.jsx'

import FeedbackBlock from './FeedbackBlock.jsx';

class FeedbackPanel extends React.Component {

    state = {
        remark: ""
    }

    static getDerivedStateFromProps(nextProps, prevState) {
        return {remark: nextProps.solution.remark}
    }

    saveRemark = () => {
        api.post('solution/' + this.props.examID + '/' + this.props.submissionID + '/' + this.props.problem.id, {
            remark: this.state.remark
        })
            .then(sucess => {
                if (!sucess) alert('Remark not saved!')
            })
    }

    changeRemark = (event) => {
        this.setState({
            remark: event.target.value
        })
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
                    <textarea className="textarea" rows="2" placeholder="remark" value={this.state.remark} onBlur={this.saveRemark} onChange={this.changeRemark} />
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