import React from 'react';

import * as api from '../../api.jsx'

class ProblemSelector extends React.Component {

    state = {
        problemList: []
    }

    componentDidMount = () => {
        api.get('problems/' + this.props.examID)
            .then(problems => {
                this.setState({
                    problemList: problems
                }, this.props.changeProblem(problems[0].id))
            })

    }

    render() {
        return (
            <div className="field">
                <label className="label">Problem:</label>
                <div className="control has-icons-left">
                    <div className="select is-fullwidth">
                        <select value={this.props.name}
                            onChange={(event) => this.props.changeProblem(event.target.value)}>
                            {this.state.problemList.map(problem =>
                                <option key={problem.id} value={problem.id}>{problem.name}</option>
                            )}

                        </select>
                    </div>
                    <span className="icon is-left">
                        <i className="fa fa-question"></i>
                    </span>
                    <br />
                </div>
            </div>
        )
    }


}

export default ProblemSelector;