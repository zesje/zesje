import React from 'react';
import NavBar from '../components/NavBar';
import Hero from '../components/Hero';
import Footer from '../components/Footer';

import test_image from '../student.jpg';

import getClosest from 'get-closest';
import Fuse from 'fuse.js';

class CheckStudents extends React.Component {

    constructor(props) {
        super(props)

        this.state = {
            search: {
                input: 'Thomas',
                result: [
                    {
                        id:4492242,
                        first_name:'Thomas',
                        last_name:'Roos',
                        email:'mail@thomasroos.nl'
                    },
                    {
                        id:1234567,
                        first_name:'John',
                        last_name:'Doe',
                        email:'Jonnie@doe.com'
                    }
                ]
            },
            exam: {
                id: 0,
                name: 'Midterm 1 5-12',
                available: [
                    {
                        id:0,
                        name:'Midterm 1 5-12',
                    },
                    {
                        id:1,
                        name:'Midterm 2 5-1'
                    },
                    {
                        id:2,
                        name:'Final exam 20-2'
                    }
                ]
            },
            submission: {
                id: 0,
                index: 0,
                input: 0,
                imagePath: test_image,
                available: [
                    {
                        id: 0,
                        checked: true
                    },
                    {
                        id: 1,
                        checked:true
                    },
                    {
                        id: 50,
                        checked:false
                    },
                    {
                        id: 51,
                        checked:false
                    },
                    {
                        id: 64,
                        checked:false
                    },
                    {
                        id: 146,
                        checked:false
                    },
                    {
                        id: 1465,
                        checked:false
                    },
                    {
                        id: 1466,
                        checked:false
                    },
                    {
                        id: 1467,
                        checked:false
                    }
                ]
            },
            students: [
                {
                    id:4492242,
                    first_name:'Thomas',
                    last_name:'Roos',
                    email:'mail@thomasroos.nl'
                },
                {
                    id:1234567,
                    first_name:'John',
                    last_name:'Doe',
                    email:'Jonnie@doe.com'
                }
            ]   
        }

        this.search = this.search.bind(this);
        this.setSubmission = this.setSubmission.bind(this);
        this.prev = this.prev.bind(this);
        this.prevUnchecked = this.prevUnchecked.bind(this);
        this.next = this.next.bind(this);
        this.nextUnchecked = this.nextUnchecked.bind(this);
        this.setSubInput = this.setSubInput.bind(this);

    }

    prev() {
        var newIndex = this.state.submission.index - 1;

        if (newIndex >= 0 && newIndex < this.state.submission.available.length) {
            this.setState({
                submission: {
                    ...this.state.submission,
                    input: this.state.submission.available[newIndex].id
                }
            },this.setSubmission)
        }
    }
    next() {
        var newIndex = this.state.submission.index + 1;

        if (newIndex >= 0 && newIndex < this.state.submission.available.length) {
            this.setState({
                submission: {
                    ...this.state.submission,
                    input: this.state.submission.available[newIndex].id
                }
            },this.setSubmission)
        }
        
    }

    prevUnchecked() {
        var unchecked = this.state.submission.available.filter(sub => sub.checked === true).map(sub => sub.id);
        var newInput = getClosest.lowerNumber(this.state.submission.id - 1, unchecked);

        if (typeof newInput !== 'undefined') {
            this.setState({
                submission: {
                    ...this.state.submission,
                    input: newInput
                }
            }, this.setSubmission)
        }
    }
    nextUnchecked(){
        var unchecked = this.state.submission.available.filter(sub => sub.checked === true).map(sub => sub.id);
        var newInput = getClosest.greaterNumber(this.state.submission.id + 1, unchecked);

        if (typeof newInput !== 'undefined') {
            this.setState({
                submission: {
                    ...this.state.submission,
                    input: newInput
                }
            }, this.setSubmission)
        }
    }

    search(event) {

        var options = {
            shouldSort: true,
            threshold: 0.6,
            location: 0,
            distance: 100,
            maxPatternLength: 32,
            minMatchCharLength: 1,
            keys: [
                "id",
                "first_name",
                "last_name"
            ]
        };
        var fuse = new Fuse(this.state.students, options);
        var result = fuse.search(event.target.value);

        this.setState({
            search: {
                input: event.target.value,
                result: result
            }
        })
    }

    setSubmission() {

        var input = this.state.submission.input;
        var i = this.state.submission.available.findIndex(sub => sub.id === input);

        if (i >= 0) {
            this.setState({
                submission:
                    {
                        ...this.state.submission,
                        id: parseInt(input),
                        index: i
                    }
            })
        } else {
            this.setState({
                submission:
                    {
                        ...this.state.submission,
                        input: this.state.submission.id
                    }
            })
            alert('Could not find that submission number :(\nSorry!');
        }
    }

    setSubInput(event) {
        var patt = new RegExp(/^([1-9]\d*|0)?$/);

        if (patt.test(event.target.value)) {
            this.setState({
                submission:
                    {
                        ...this.state.submission,
                        input: parseInt(event.target.value)
                    }
            })
        }
        
        
    }

    render() {
        var inputStyle = {
            width: '5em'
        };

        var total = this.state.submission.available.length;
        var checked = this.state.submission.available.filter(sub => sub.checked).length;
        var percentage = ((checked / total) * 100).toFixed(1);

        var maxSubmission = Math.max(...this.state.submission.available.map(o => o.id));

        return (
            <div>

                <NavBar />

                <Hero title='Match Students' subtitle='Who made what?' />

                <section className="section">

                    <div className="container">

                        <div className="columns">
                            <div className="column is-one-quarter-desktop is-one-third-tablet">

                                <div className="is-hidden-desktop">
                                    <div className="control has-icons-left">
                                        <div className="select is-info is-fullwidth">
                                            <select>
                                                {this.state.exam.available.map(exam => 
                                                    <option key={exam.id}>{exam.name}</option>
                                                )}
                                            </select>
                                        </div>
                                        <span className="icon is-small is-left">
                                            <i className="fa fa-pencil"></i>
                                        </span>
                                    </div>
                                </div>

                                <nav className="panel">
                                    <p className="panel-heading">
                                        Students
                                    </p>
                                    <p className="panel-tabs">
                                        <a className="is-active">Unassigned</a>
                                        <a>all</a>
                                    </p>
                                    <div className="panel-block">
                                        <p className="control has-icons-left">
                                            <input className="input" type="text" placeholder="Search"
                                                value={this.state.search.input} onChange={this.search}/>
                                            <span className="icon is-left">
                                                <i className="fa fa-search"></i>
                                            </span>
                                        </p>
                                    </div>
                                    {this.state.search.result.map(student => 
                                        <a className="panel-block is-active" key={student.id}>
                                        <span className="panel-icon">
                                            <i className="fa fa-user"></i>
                                        </span>
                                        {student.first_name + ' ' + student.last_name}
                                        </a>
                                    )}

                                    <div className="panel-block is-hidden-mobile">
                                        <button className="button is-link is-outlined is-fullwidth">
                                            Batch upload
                                        </button>
                                    </div>
                                </nav>
                            </div>

                            <div className="column">

                                <div className="level">

                                    <div className="level-left is-hidden-touch">
                                        <div className="level-item">
                                            <div className="control has-icons-left">
                                                <div className="select is-info is-fullwidth">
                                                    <select>
                                                        {this.state.exam.available.map(exam => 
                                                            <option key={exam.id}>{exam.name}</option>
                                                        )}
                                                    </select>
                                                </div>
                                                <span className="icon is-small is-left">
                                                    <i className="fa fa-pencil"></i>
                                                </span>
                                            </div>
                                        </div>
                                    </div>

                                    <div className="level-right">
                                        <div className="level-item">
                                            <div className="field has-addons is-mobile">
                                                <div className="control">
                                                    <button type="submit" className="button is-info is-rounded is-hidden-mobile"
                                                        onClick={this.prevUnchecked}>unchecked</button>
                                                    <button type="submit" className="button" onClick={this.prev} >Previous</button>
                                                </div>
                                                <div className="control">
                                                    <input className="input is-rounded has-text-centered" type="text"
                                                        pattern="/^([1-9]\d*|0)$/" value={this.state.submission.input}
                                                        onChange={this.setSubInput} onSubmit={this.setSubmission}
                                                        onBlur={this.setSubmission} maxLength="4" size="6" style={inputStyle} />
                                                </div>
                                                <div className="control">
                                                    <button type="submit" className="button" onClick={this.next}>Next</button>
                                                    <button type="submit" className="button is-info is-rounded is-hidden-mobile"
                                                        onClick={this.nextUnchecked}>unchecked</button>
                                                </div>
                                            </div>
                                        </div>
                                    </div>

                                </div>

                                <div className="level is-mobile">
                                    <div className="level-item is-hidden-mobile">
                                        <progress className="progress is-success" value={checked}
                                            max={total}>
                                            {percentage}%</progress>
                                    </div>
                                    <div className="level-right">
                                        <div className="level-item has-text-grey">
                                            <i>{checked} / {total}</i>
                                        </div>
                                        <div className="level-item has-text-success">
                                            <b>{percentage}%</b>
                                        </div>
                                    </div>
                                </div>

                                <p className="box">
                                    <img src={test_image} />
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