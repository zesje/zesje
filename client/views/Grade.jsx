import React from 'react';
import getClosest from 'get-closest';

import Hero from '../components/Hero.jsx';

import FeedbackPanel from './grade/FeedbackPanel.jsx';
import ProblemSelector from './grade/ProblemSelector.jsx';
import EditPanel from './grade/EditPanel.jsx';
const ProgressBar = () => null;

import * as api from '../api.jsx';


class Grade extends React.Component {

    state = {
        editActive: false,
        editFeedback: null,
        sIndex: 0,
        pIndex: 0,
        input: "",
        examID: null
    }

    prev = () => {
        const newIndex = this.state.sIndex - 1;

        if (newIndex >= 0 && newIndex < this.props.exam.submissions.length) {
            this.setState({
                sIndex: newIndex,
                input: this.props.exam.submissions[newIndex].student.id  + ' (' + 
                    this.props.exam.submissions[newIndex].student.firstName + ' ' + this.props.exam.submissions[newIndex].student.lastName + ')'
            })
            this.props.updateSubmission(newIndex)
        }
    }
    next = () => {
        const newIndex = this.state.sIndex + 1;

        if (newIndex >= 0 && newIndex < this.props.exam.submissions.length) {
            this.setState({
                sIndex: newIndex,
                input: this.props.exam.submissions[newIndex].student.id + ' (' + 
                    this.props.exam.submissions[newIndex].student.firstName + ' ' + this.props.exam.submissions[newIndex].student.lastName + ')'
            })
            this.props.updateSubmission(newIndex)
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
            this.setState({
                index: i,
                input: sub.student.id  + ' (' + sub.student.firstName + ' ' + sub.student.lastName + ')'
            })
            this.props.updateSubmission(i)
        } else {
            this.setState({
                input: this.props.exam.submissions[this.state.sIndex].student.id  + ' (' + 
                    this.props.exam.submissions[this.state.sIndex].student.firstName + ' ' + this.props.exam.submissions[this.state.sIndex].student.lastName + ')'
            })
            alert('Could not find that submission number :(\nSorry!');
        }
    }
    changeProblem = (event) => {
        console.log(event.target.value);
        this.setState({
            pIndex: event.target.value
        })
    }
    static getDerivedStateFromProps = (newProps, prevState) => {
        console.log('Nieuwe props')
        if (newProps.exam.id != prevState.examID && newProps.exam.submissions.length) {
            return {
                input: newProps.exam.submissions[0].student.id + ' (' + 
                    newProps.exam.submissions[0].student.firstName + ' ' + newProps.exam.submissions[0].student.lastName + ')',
                sIndex: 0,
                pIndex: 0,
                examID: newProps.exam.id
            }
        }
        return {
            input: newProps.exam.submissions[prevState.sIndex].student.id + ' (' + 
            newProps.exam.submissions[prevState.sIndex].student.firstName + ' ' + newProps.exam.submissions[prevState.sIndex].student.lastName + ')'
        }
    }

    render() {



        return (
            <div>

                <Hero title='Grade' subtitle='This is where the magic happens!' />

                <section className="section">

                    <div className="container">
                        <div className="columns">
                            <div className="column is-one-quarter-desktop is-one-third-tablet">
                                <ProblemSelector problems={this.props.exam.problems} changeProblem={this.changeProblem}/>
                                {this.state.editActive ?
                                    <EditPanel problem={this.props.exam.problems[this.state.pIndex]} editFeedback={this.state.editFeedback} toggleEdit={this.toggleEdit}/>
                                    :
                                    <FeedbackPanel problem={this.props.exam.problems[this.state.pIndex]} solution={this.props.exam.submissions[this.state.sIndex]}
                                        toggleEdit={this.toggleEdit} />
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

                                <p className="box">
                                    <img src={this.props.exam.id ? ('api/images/solutions/' + this.props.exam.id + '/' 
                                        + this.props.exam.problems[this.state.pIndex].id + '/' + this.props.exam.submissions[this.state.sIndex].id) : ''} alt="" />
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