import React from 'react';

import Hero from '../components/Hero.jsx';

import FeedbackPanel from './grade/FeedbackPanel.jsx';
import ProblemSelector from './grade/ProblemSelector.jsx';
import EditPanel from './grade/EditPanel.jsx';
const ProgressBar = () => null;

class Grade extends React.Component {

    state = {
        editActive: false,
        editFeedback: null,
        problem: null,
        submission: {
            input: "",
            imagePath: ""
        },
        solution: null
    }

    prev = () => {

    }
    next = () => {

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

    }
    changeProblem = (id) => {
        console.log(id);
        this.setState({
            problem: id
        })
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
                                                    onChange={this.setSubInput} onSubmit={this.setSubmission}/>
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