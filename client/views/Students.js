import React from 'react';
import NavBar from '../components/NavBar';
import Hero from '../components/Hero';
import Footer from '../components/Footer';
import * as api from '../api';

import test_image from '../student.jpg';

import getClosest from 'get-closest';
import Fuse from 'fuse.js';

const StudentPanelBlock = (props) => {
	return (
		<div key={props.student.id}>
			<a className={"panel-block" + (props.selected ? " button is-link" : " is-active")}
				key={props.student.id} id={props.student.id} selected={props.selected} onClick={props.selectStudent}>
				<span className={"panel-icon" + (props.selected ? " has-text-white" : "")}>
					<i className="fa fa-user"></i>
				</span>
				{props.student.first_name + ' ' + props.student.last_name}
			</a>

			<div className={"panel-block" + (props.selected ? " is-info" : " is-hidden")}
				key="info" style={{ backgroundColor: '#dbdbdb' }}>

				<span className="panel-icon">
					<i className="fa fa-database"></i>
				</span>
				{props.student.id}&emsp;
            <span className="panel-icon">
					<i className="fa fa-check"></i>
					{/* TODO: Make icon respond to possible submissions of student */}
				</span>
				<i>assigned</i>
			</div>

		</div>
	)
}

const ProgressBar = (props) => {
	var total = props.submissions.length;
	var checked = props.submissions.filter(sub => sub.validated).length;
	var percentage = ((checked / total) * 100).toFixed(1);

	return (
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
	)
}

const ExamSelector = (props) => (
	<div className="control has-icons-left">
		<div className="select is-info is-fullwidth">
			<select value={props.exam.name} onChange={props.selectExam}>
				{props.exam.list.map(ex =>
					<option key={ex.id}>{ex.name}</option>
				)}
			</select>
		</div>
		<span className="icon is-small is-left">
			<i className="fa fa-pencil"></i>
		</span>
	</div>
)


class CheckStudents extends React.Component {


	students = [];

	state = {
		search: {
			input: '',
			selected: 0,
			result: []
		},
		exam: {
			id: 0,
			name: "Loading...",
			list: []
		},
		submission: {
			id: 0,
			input: 0,
			index: 0,
			studentID: null,
			validated: false,
			imagePath: test_image,
			list: []
		}
	};

	componentDidMount() {
		api.get('exams')
			.then(exams => {
				this.setState({
					exam: {
						id: exams[0].id,
						name: exams[0].name,
						list: exams
					}
				}, this.getSubmissions)
			})
			.catch(err => {
				alert('failed to get exams (see javascript console for details)')
				console.error('failed to get exams:', err)
				throw err
			})

		api.get('students')
			.then(students => {
				this.students = students;
			})
			.catch(err => {
				alert('failed to get students (see javascript console for details)')
				console.error('failed to get students:', err)
				throw err
			})

	}


	prev = () => {
		var newIndex = this.state.submission.index - 1;

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
		var newIndex = this.state.submission.index + 1;

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
		var unchecked = this.state.submission.list.filter(sub => sub.validated === false).map(sub => sub.id);
		var newInput = getClosest.lowerNumber(this.state.submission.id - 1, unchecked);

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
		var unchecked = this.state.submission.list.filter(sub => sub.validated === false).map(sub => sub.id);
		var newInput = getClosest.greaterNumber(this.state.submission.id + 1, unchecked);

		if (typeof newInput !== 'undefined') {
			this.setState({
				submission: {
					...this.state.submission,
					input: unchecked[newInput]
				}
			}, this.setSubmission)
		}
	}
	// TODO: Let the submission picture be updated!

	search = (event) => {

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
		var fuse = new Fuse(this.students, options);
		var result = fuse.search(event.target.value).slice(0, 10);

		this.setState({
			search: {
				input: event.target.value,
				selected: 0,
				result: result
			}
		})
	}

	setSubmission = () => {

		var input = parseInt(this.state.submission.input);
		console.log(input);
		var i = this.state.submission.list.findIndex(sub => sub.id === input);

		if (i >= 0) {
			this.setState({
				submission: {
					...this.state.submission,
					id: input,
					index: i
				}
			})
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
		var patt = new RegExp(/^([1-9]\d*|0)?$/);

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
		var id = this.state.exam.list.findIndex(ex => ex.name === event.target.value);
		this.setState({
			exam: {
				...this.state.exam,
				id: id,
				name: event.target.value
			}
		}, this.getSubmissions)
	}

	getSubmissions() {
		api.get('submissions/' + this.state.exam.id)
			.then(submissions => {
				this.setState({
					submission: {
						...this.state.submission,
						id: submissions[0].id,
						input: submissions[0].id,
						studentID: submissions[0].studentID,
						validated: submissions[0].validated,
						list: submissions
					}
				})
			})
			.catch(err => {
				alert('failed to get submissions (see javascript console for details)')
				console.error('failed to get submissions:', err)
				throw err
			})
	}

	moveSelection = (event) => {
		if (event.keyCode == 38 || event.keyCode == 40) {
			event.preventDefault();
			var sel = this.state.search.selected;

			if (event.keyCode == 38 && sel > 0) sel--;
			if (event.keyCode == 40 && sel < this.state.search.result.length - 1) sel++;

			this.setState({
				search: {
					...this.state.search,
					selected: sel
				}
			})
		}
	}

	selectStudent = (event) => {

		if (event.target.selected) {
			// TODO: Send student ID to server
		} else {
			var index = this.state.search.result.findIndex(result => result.id == event.target.id);
			this.setState({
				search: {
					...this.state.search,
					selected: index
				}
			})
		}
	}

	render() {
		var inputStyle = {
			width: '5em'
		};

		var maxSubmission = Math.max(...this.state.submission.list.map(o => o.id));

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
											<input className="input" type="text" autoFocus placeholder="Search"
												value={this.state.search.input} onChange={this.search} onKeyDown={this.moveSelection} />
											<span className="icon is-left">
												<i className="fa fa-search"></i>
											</span>
										</p>
									</div>
									{this.state.search.result.map((student, index) =>
										<StudentPanelBlock key={student.id} student={student}
											selected={index === this.state.search.selected} selectStudent={this.selectStudent} />
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
											<ExamSelector exam={this.state.exam} selectExam={this.selectExam} />
										</div>
									</div>

									<div className="level-right">
										<div className="level-item">
											<div className="field has-addons is-mobile">
												<div className="control">
													<button type="submit" className="button is-info is-rounded is-hidden-mobile"
														onClick={this.prevUnchecked}>unchecked</button>
													<button type="submit" className="button" onClick={this.prev}>Previous</button>
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

								<ProgressBar submissions={this.state.submission.list} />

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