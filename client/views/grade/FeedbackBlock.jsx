import React from 'react';

class FeedbackBlock extends React.Component {


    render() {
        return (
            <a className="panel-block is-active" onClick={this.props.onClick} >
                <span className="panel-icon">
                    <i className={"fa fa-" + (this.props.checked ? "check-square-o" : "square-o")}></i>
                </span>
                <div style={{ width: '80%' }}>
                    {this.props.feedback.name}
                </div>
                <i>{this.props.feedback.score}</i>
            </a>
        )
    }
}


export default FeedbackBlock;