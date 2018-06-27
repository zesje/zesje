import React from 'react';
import getClosest from 'get-closest';

import Hero from '../components/Hero.jsx';

import FeedbackPanel from './grade/FeedbackPanel.jsx';
import ProblemSelector from './grade/ProblemSelector.jsx';
import EditPanel from './grade/EditPanel.jsx';
const ProgressBar = () => null;


class Grade extends React.Component {

    state = {
        editActive: false,
        editFeedback: null,
        sIndex: 0,
        pIndex: 0,
        input: "",
        examID: null
    }

    static inputString (sub) {
        if(sub.student) {
            return (sub.student.id + ' (' + sub.student.firstName + ' ' + sub.student.lastName + ')')
        }
        return ('#' + sub.id)
    }

    prev = () => {
        const newIndex = this.state.sIndex - 1;

        if (newIndex >= 0 && newIndex < this.props.exam.submissions.length) {
            this.props.updateSubmission(newIndex)
            this.setState({
                sIndex: newIndex,
                input: Grade.inputString(this.props.exam.submissions[newIndex])
            })
        }
    }
    next = () => {
        const newIndex = this.state.sIndex + 1;

        if (newIndex >= 0 && newIndex < this.props.exam.submissions.length) {
            this.props.updateSubmission(newIndex)
            this.setState({
                sIndex: newIndex,
                input: Grade.inputString(this.props.exam.submissions[newIndex])
            })
        }
    }

    prevUngraded = () => {

    }
    nextUngraded = () => {

    }

    toggleEdit = () => {
        this.setState({
            editActive: !this.state.editActive,
            editFeedback: null
        })
    }

    setSubInput = (event) => {
        this.setState({ input: event.target.value })
    }
    setSubmission = () => {
        const input = parseInt(this.state.input);
        const i = this.state.submission.list.findIndex(sub => sub.student.id === input);
        const sub = this.state.submission.list[i];

        if (i >= 0) {
            this.props.updateSubmission(i)
            this.setState({
                index: i,
                input: Grade.inputString(sub)
            })
        } else {
            this.setState({
                input: Grade.inputString(this.props.exam.submissions[this.state.sIndex])
            })
            alert('Could not find that submission number :(\nSorry!');
        }
    }
    changeProblem = (event) => {
        this.setState({
            pIndex: event.target.value
        })
    }
    static getDerivedStateFromProps = (newProps, prevState) => {
        if (newProps.exam.id != prevState.examID && newProps.exam.submissions.length) {
            return {
                input: Grade.inputString(newProps.exam.submissions[0]),
                sIndex: 0,
                pIndex: 0,
                examID: newProps.exam.id
            }
        }
        return {
            input: Grade.inputString(newProps.exam.submissions[prevState.sIndex])
        }
    }

    render() {
        const submission = this.props.exam.submissions[this.state.sIndex];
        const solution = submission.problems[this.state.pIndex];
        const problem = this.props.exam.problems[this.state.pIndex];

        return (
            <div>

                <Hero title='Grade' subtitle='Assign feedback to each solution' />

                <section className="section">

                    <div className="container">
                        <div className="columns">
                            <div className="column is-one-quarter-desktop is-one-third-tablet">
                                <ProblemSelector problems={this.props.exam.problems} changeProblem={this.changeProblem}/>
                                {this.state.editActive ?
                                    <EditPanel problem={problem} editFeedback={this.state.editFeedback} toggleEdit={this.toggleEdit}/>
                                    :
                                    <FeedbackPanel examID={this.props.exam.id} submissionID={submission.id}
                                        problem={problem} solution={solution} graderID={this.props.graderID}
                                        toggleEdit={this.toggleEdit} updateSubmission={() => this.props.updateSubmission(this.state.sIndex)} />
                                }
                            </div>

                            <div className="column">
                                <div className="level">
                                    <div className="level-item">
                                        <div className="field has-addons is-mobile">
                                            <div className="control">
                                                <button type="submit" className="button is-info is-rounded is-hidden-mobile"
                                                    onClick={this.prevUngraded}>ungraded</button>
                                                <button type="submit" className="button is-link"
                                                    onClick={this.prev}>Previous</button>
                                            </div>
                                            <div className="control">
                                                <input className="input is-rounded has-text-centered is-link"
                                                    value={this.state.input} type="text"
                                                    onChange={this.setSubInput} onSubmit={this.setSubmission} onBlur={this.setSubmission} />
                                            </div>
                                            <div className="control">
                                                <button type="submit" className="button is-link"
                                                    onClick={this.next}>Next</button>
                                                <button type="submit" className="button is-info is-rounded is-hidden-mobile"
                                                    onClick={this.nextUngraded}>ungraded</button>
                                            </div>
                                        </div>
                                    </div>
                                </div>

                                <ProgressBar submissions={this.props.exam.submissions} />
                                {solution.graded_at ?
                                    <div>Graded by: {solution.graded_by.name} <i>({solution.graded_at})</i></div>
                                    :
                                    <div>Ungraded</div>
                                }
                                <p className="box">
                                    <img src={this.props.exam.id ? ('api/images/solutions/' + this.props.exam.id + '/' 
                                        + this.props.exam.problems[this.state.pIndex].id + '/' + submission.id) : ''} alt="" />
                                </p>

                            </div>
                        </div>
                    </div>
                </section>

            </div>
        )
    }
}

export default Grade;
