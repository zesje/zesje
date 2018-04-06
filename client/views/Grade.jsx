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
        problem: null,
        submission: {
            input: "",
            index: 0,
            id: null,
            student: null,
            validated: false,
            imagePath: null,
            list: []
        },
        solution: null
    }

    prev = () => {
        const newIndex = this.state.submission.index - 1;

        if (newIndex >= 0 && newIndex < this.state.submission.list.length) {
            this.setState({
                submission: {
                    ...this.state.submission,
                    input: this.state.submission.list[newIndex].student.id
                }
            }, this.setSubmission)
        }
    }
    next = () => {
        const newIndex = this.state.submission.index + 1;

        if (newIndex >= 0 && newIndex < this.state.submission.list.length) {
            this.setState({
                submission: {
                    ...this.state.submission,
                    input: this.state.submission.list[newIndex].student.id
                }
            }, this.setSubmission)
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
    editFeedback = (event) => {
        console.log(event);
        this.setState({
            editActive: true
        })
    }

    setSubInput = (event) => {
        this.setState({
            submission: {
                ...this.state.submission,
                input: event.target.value
            }
        })
    }
    setSubmission = () => {
        const input = parseInt(this.state.submission.input);
        const i = this.state.submission.list.findIndex(sub => sub.student.id === input);
        const sub = this.state.submission.list[i];

        if (i >= 0) {
            this.setState({
                submission: {
                    ...this.state.submission,
                    input: sub.student.id + ' (' + sub.student.firstName + ')',
                    id: sub.id,
                    index: i,
                    student: sub.student,
                    validated: sub.validated,
                    imagePath: 'api/images/solutions/' + this.props.exam.id + '/' + this.state.problem + '/' + sub.id                    
                }
            }, this.getSubmission)
        } else {
            this.setState({
                submission: {
                    ...this.state.submission,
                    input: this.state.submission.student.id
                }
            })
            alert('Could not find that submission number :(\nSorry!');
        }
    }
    changeProblem = (id) => {
        console.log(id);
        this.setState({
            problem: id,
            submission: {
                ...this.state.submission,
                imagePath: 'api/images/solutions/' + this.props.exam.id + '/' + id + '/' + this.state.submission.id
            }
        })
    }

    componentDidMount = () => {
        api.get('submissions/' + this.props.exam.id)
            .then(subs => 
            this.setState({
                submission: {
                    input: subs[0].student.id + ' (' + subs[0].student.firstName + ')',
                    index: 0,
                    id: subs[0].id,
                    student: subs[0].student,
                    validated: subs[0].validated,
                    imagePath: 'api/images/solutions/' + this.props.exam.id + '/' + this.state.problem + '/' + subs[0].id,
                    list: subs
                }
            }))
    }


    render() {



        return (
            <div>

                <Hero title='Grade' subtitle='This is where the magic happens!' />

                <section className="section">

                    <div className="container">
                        <div className="columns">
                            <div className="column is-one-quarter-desktop is-one-third-tablet">
                                <ProblemSelector examID={this.props.exam.id} changeProblem={this.changeProblem}/>
                                {this.state.editActive ?
                                    <EditPanel problem={this.state.problem} feedbackID={this.state.editFeedback} toggleEdit={this.toggleEdit}/>
                                    :
                                    <FeedbackPanel problem={this.state.problem} toggleEdit={this.toggleEdit} 
                                        editFeedback={this.editFeedback}/>
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
                                                    value={this.state.submission.input} type="text"
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

                                <ProgressBar submissions={this.state.submission} />

                                <p className="box">
                                    <img src={this.state.submission.imagePath} alt="" />
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