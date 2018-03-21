import React from 'react';
import getClosest from 'get-closest';
import Mousetrap from 'mousetrap';

import Hero from '../components/Hero.jsx';

import * as api from '../api.jsx';

import ProgressBar from './students/ProgressBar.jsx';
import SearchPanel from './students/SearchPanel.jsx';
import EditPanel from './students/EditPanel.jsx';

class CheckStudents extends React.Component {

    state = {
        editActive: false,
        editStud: null,
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
    };

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

        this.loadSubmissions();

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
                    imagePath: 'api/images/signature/' + this.props.exam.id + '/' + input
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

    getSubmission = () => {
        api.get('submissions/' + this.props.exam.id + '/' + this.state.submission.id)
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
                }, this.listMatchedStudent)
            })
            .catch(err => {
                alert('failed to get submission (see javascript console for details)')
                console.error('failed to get submission:', err)
                throw err
            })
    }

    loadSubmissions = () => {
        api.get('submissions/' + this.props.exam.id)
            .then(subs => {
                if (subs.length) {
                    this.setState({
                        submission: {
                            ...this.state.submission,
                            id: subs[0].id,
                            input: subs[0].id,
                            studentID: subs[0].studentID,
                            validated: subs[0].validated,
                            imagePath: 'api/images/signature/' + this.props.exam.id + '/' + subs[0].id,
                            list: subs
                        }
                    }, this.listMatchedStudent)
                } else {
                    alert('This exam has no submissions :(')
                }
            })
            .catch(err => {
                alert('failed to get submissions (see javascript console for details)')
                console.error('failed to get submissions:', err)
                throw err
            })
    }

    listMatchedStudent = () => {
        if (this.search) this.search.listMatchedStudent();
    };

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

        api.put('submissions/' + this.props.exam.id + '/' + this.state.submission.id, { studentID: studID })
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

    toggleEdit = (student) => {
        if (student && student.id) {
            this.setState({
                editActive: true,
                editStud: student
            })
        } else {
            this.setState({
                editActive: !this.state.editActive,
                editStud: null
            })
        }
    }

    render() {
        const inputStyle = {
            width: '5em'
        };

        const maxSubmission = Math.max(...this.state.submission.list.map(o => o.id));

        return (
            <div>

                <Hero title='Match Students' subtitle='Who made what?' />

                <section className="section">

                    <div className="container">

                        <div className="columns">
                            <div className="column is-one-quarter-desktop is-one-third-tablet">
                                {this.state.editActive ?
                                    <EditPanel toggleEdit={this.toggleEdit} editStud={this.state.editStud} />
                                    :
                                    <SearchPanel ref={(search) => { this.search = search; }}
                                        matchStudent={this.matchStudent} toggleEdit={this.toggleEdit}
                                        studentID={this.state.submission.studentID} validated={this.state.submission.validated} />
                                }
                            </div>

                            <div className="column">
                                <div className="level">
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

                                <ProgressBar submissions={this.state.submission.list} />

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

export default CheckStudents;
