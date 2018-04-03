import React from 'react';

import * as api from '../../api.jsx'

import FeedbackBlock from './FeedbackBlock.jsx';

class FeedbackPanel extends React.Component {

    state = {
        feedback: []
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
        if (this.props.problem !== nextProps.problem || this.state.feedback != nextState.feedback) {
            return true;            
        } else {
            console.log('halting re-render')
            return false;
        }
    }

    render() {

        return (
            <nav className="panel">
                <p className="panel-heading">
                    Feedback
                </p>
                {this.state.feedback.map((feedback, i) =>
                    <FeedbackBlock key={i} index={i} feedback={feedback} checked={true} onClick={this.props.editFeedback} />
                )}
                <div className="panel-block is-hidden-mobile">
                    <button className="button is-link is-outlined is-fullwidth" onClick={this.props.toggleEdit}>
                        <span className="icon is-small">
                            <i className="fa fa-plus"></i>
                        </span>
                        <span>add option</span>
                    </button>
                </div>
            </nav>
        )
    }

}
export default FeedbackPanel;