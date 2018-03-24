import React from 'react';

import * as api from '../../api.jsx'

const FeedbackBlock = (props) => (
    <a className="panel-block is-active" onClick={props.onClick} >
        <span className="panel-icon">
            <i className={"fa fa-" + (props.checked ? "check-square-o" : "square-o")}></i>
        </span>
        {props.feedback.name}&nbsp;<i>- [{props.feedback.score}]</i>
    </a>
)


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