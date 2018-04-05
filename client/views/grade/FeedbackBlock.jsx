import React from 'react';

class FeedbackBlock extends React.Component {

    state = {
        hover: false
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

    componentDidMount = () => {
        console.log('mounting! ' + this.props.feedback.id)        
    }


    render() {
        const score = this.props.feedback.score;

        return (
            <a className="panel-block is-active" onClick={() => !this.state.hover && console.log('a click')} >
                <span className="panel-icon">
                    <i className={"fa fa-" + (this.props.checked ? "check-square-o" : "square-o")}></i>
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