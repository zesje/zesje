import React from 'react';
import getClosest from 'get-closest';
import Mousetrap from 'mousetrap';

import NavBar from '../components/NavBar';
import Hero from '../components/Hero';
import Footer from '../components/Footer';

import * as api from '../api';

import ProgressBar from './students/ProgressBar.jsx';
import SearchPanel from './students/SearchPanel.jsx';
import ExamSelector from './students/ExamSelector.jsx';

class CheckStudents extends React.Component {

    state = {
        exam: {
            id: 0,
            name: "Loading...",
            list: [
                {
                    id: '0',
                    name: ""
                }
            ]
        },
        submission: {
            id: 0,
            input: 0,
            index: 0,
            studentID: null,
            validated: false,
            imagePath: null,
            list: [
                {
                    id: 0,
                    studentID: 0,
                    validated: false
                }
            ]
        }
    };

    componentWillUnmount = () => {
        Mousetrap.unbind(["left", "h"]);
        Mousetrap.unbind(["right", "l"]);
        Mousetrap.unbind(["up", "k"]);
        Mousetrap.unbind(["down", "j"]);
    }

    componentDidMount = () => {

        Mousetrap.bind(["left", "h"], this.prev);
        Mousetrap.bind(["right", "l"], this.next);
        Mousetrap.bind(["up", "k"], (event) => {
            event.preventDefault();
            this.nextUnchecked();
        });
        Mousetrap.bind(["down", "j"], (event) => {
            event.preventDefault();
            this.prevUnchecked();
        });

        api.get('exams')
            .then(exams => {
                if (exams.length) {
                    this.setState({
                        exam: {
                            id: exams[0].id,
                            name: exams[0].name,
                            list: exams
                        }
                    }, this.loadSubmissions)
                }
            })
            .catch(err => {
                alert('failed to get exams (see javascript console for details)')
                console.error('failed to get exams:', err)
                throw err
            })

    }


    prev = () => {
        const newIndex = this.state.submission.index - 1;

        if (newIndex >= 0 && newIndex < this.state.submission.list.length) {
            this.setState({
                submission: {
                    ...this.state.submission,
                    input: this.state.submission.list[newIndex].id
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
                    input: this.state.submission.list[newIndex].id
                }
            }, this.setSubmission)
        }

    }

    prevUnchecked = () => {
        const unchecked = this.state.submission.list.filter(sub => sub.validated === false).map(sub => sub.id);
        const newInput = getClosest.lowerNumber(this.state.submission.id - 1, unchecked);

        if (typeof newInput !== 'undefined') {
            this.setState({
                submission: {
                    ...this.state.submission,
                    input: unchecked[newInput]
                }
            }, this.setSubmission)
        }
    }
    nextUnchecked = () => {
        const unchecked = this.state.submission.list.filter(sub => sub.validated === false).map(sub => sub.id);
        const newInput = getClosest.greaterNumber(this.state.submission.id + 1, unchecked);

        if (typeof newInput !== 'undefined') {
            this.setState({
                submission: {
                    ...this.state.submission,
                    input: unchecked[newInput]
                }
            }, this.setSubmission)
        }
    }

    setSubmission = () => {

        const input = parseInt(this.state.submission.input);
        const i = this.state.submission.list.findIndex(sub => sub.id === input);
        const sub = this.state.submission.list[i];

        if (i >= 0) {
            this.setState({
                submission: {
                    ...this.state.submission,
                    id: input,
                    studentID: sub.studentID,
                    validated: sub.validated,
                    index: i,
                    imagePath: 'api/images/signature/' + this.state.exam.id + '/' + input
                }
            }, this.getSubmission)
        } else {
            this.setState({
                submission: {
                    ...this.state.submission,
                    input: this.state.submission.id
                }
            })
            alert('Could not find that submission number :(\nSorry!');
        }
    }

    setSubInput = (event) => {
        const patt = new RegExp(/^([1-9]\d*|0)?$/);

        if (patt.test(event.target.value)) {
            this.setState({
                submission: {
                    ...this.state.submission,
                    input: event.target.value
                }
            })
        }
    }

    selectExam = (event) => {
        const id = this.state.exam.list.findIndex(ex => ex.name === event.target.value);
        this.setState({
            exam: {
                ...this.state.exam,
                id: id + 1,  // exam IDs are 1-based and the exam list is 0-based
                name: event.target.value
            }
        }, this.loadSubmissions)
    }

    getSubmission = () => {
        api.get('submissions/' + this.state.exam.id + '/' + this.state.submission.id)
            .then(sub => {
                let newList = this.state.submission.list;
                const index = newList.findIndex(localSub => localSub.id === sub.id)
                newList[index] = sub;
                this.setState({
                    submission: {
                        ...this.state.submission,
                        studentID: sub.studentID,
                        validated: sub.validated,
                        list: newList
                    }
                }, this.search.listMatchedStudent)
            })
            .catch(err => {
                alert('failed to get submission (see javascript console for details)')
                console.error('failed to get submission:', err)
                throw err
            })
    }

    loadSubmissions = () => {
        api.get('submissions/' + this.state.exam.id)
            .then(subs => {
                this.setState({
                    submission: {
                        ...this.state.submission,
                        id: subs[0].id,
                        input: subs[0].id,
                        studentID: subs[0].studentID,
                        validated: subs[0].validated,
                        imagePath: 'api/images/signature/' + this.state.exam.id + '/' + subs[0].id,
                        list: subs
                    }
                }, this.search.listMatchedStudent)
            })
            .catch(err => {
                alert('failed to get submissions (see javascript console for details)')
                console.error('failed to get submissions:', err)
                throw err
            })
    }

    matchStudent = (studID) => {

        let newList = this.state.submission.list;
        const index = this.state.submission.index;

        this.setState({
            submission: {
                ...this.state.submission,
                studentID: studID,
                validated: true
            }
        }, this.nextUnchecked)

        api.put('submissions/' + this.state.exam.id + '/' + this.state.submission.id, { studentID: studID })
            .then(sub => {
                newList[index] = sub;
                this.setState({
                    submission: {
                        ...this.state.submission,
                        list: newList
                    }
                })
            })
            .catch(err => {
                alert('failed to put submission (see javascript console for details)')
                console.error('failed to put submission:', err)
                throw err
            })
    }

    render() {
        const inputStyle = {
            width: '5em'
        };

        const maxSubmission = Math.max(...this.state.submission.list.map(o => o.id));

        return (
            <div>

                <NavBar />

                <Hero title='Match Students' subtitle='Who made what?' />

                <section className="section">

                    <div className="container">

                        <div className="columns">
                            <div className="column is-one-quarter-desktop is-one-third-tablet">

                                <div className="is-hidden-desktop">
                                    <ExamSelector exam={this.state.exam} selectExam={this.selectExam} />
                                </div>

                                <SearchPanel ref={(search) => { this.search = search; }}
                                    matchStudent={this.matchStudent}
                                    studentID={this.state.submission.studentID} validated={this.state.submission.validated} />


                            </div>

                            <div className="column">
                                <div className="level">

                                    <div className="level-left is-hidden-touch">
                                        <div className="level-item">
                                            <ExamSelector exam={this.state.exam} selectExam={this.selectExam} />
                                        </div>
                                    </div>

                                    <div className="level-right">
                                        <div className="level-item">
                                            <div className="field has-addons is-mobile">
                                                <div className="control">
                                                    <button type="submit" className="button is-info is-rounded is-hidden-mobile"
                                                        onClick={this.prevUnchecked}>unchecked</button>
                                                    <button type="submit" className={"button" + (this.state.submission.validated ? " is-success" : " is-link")}
                                                        onClick={this.prev}>Previous</button>
                                                </div>
                                                <div className="control">
                                                    <input className={"input is-rounded has-text-centered" + (this.state.submission.validated ? " is-success" : " is-link")}
                                                        value={this.state.submission.input} type="text"
                                                        onChange={this.setSubInput} onSubmit={this.setSubmission}
                                                        onBlur={this.setSubmission} maxLength="4" size="6" style={inputStyle} />
                                                </div>
                                                <div className="control">
                                                    <button type="submit" className={"button" + (this.state.submission.validated ? " is-success" : " is-link")}
                                                        onClick={this.next}>Next</button>
                                                    <button type="submit" className="button is-info is-rounded is-hidden-mobile"
                                                        onClick={this.nextUnchecked}>unchecked</button>
                                                </div>
                                            </div>
                                        </div>
                                    </div>
                                </div>

                                <ProgressBar submissions={this.state.submission.list} />

                                <p className="box">
                                    <img src={this.state.submission.imagePath} alt="" />
                                </p>

                            </div>
                        </div>
                    </div>
                </section>

                <Footer />

            </div>
        )
    }
}

export default CheckStudents;
