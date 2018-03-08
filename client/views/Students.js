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
	var checked = props.submissions.filter(sub => sub.checked).length;
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


	students = [
		{
			id: 4492242,
			first_name: 'Thomas',
			last_name: 'Roos',
			email: 'mail@thomasroos.nl'
		},
		{
			id: 1234567,
			first_name: 'John',
			last_name: 'Doe',
			email: 'Jonnie@doe.com'
		},
		{
			id: 44720570,
			first_name: 'Martijn',
			last_name: 'Noordhuis',
			email: 'martijnnoordhuis@gmail.com'
		},
		{
			id: 42049824,
			first_name: 'Pieter',
			last_name: 'Bas Veenhuis',
			email: 'pietertje@tudelft.nl'
		},
		{
			id: 44938843,
			first_name: 'Jurrian',
			last_name: 'Enzerink',
			email: 'jurrie98@student.tudelft.nl'
		},
		{
			id: 99998888,
			first_name: 'Kobus',
			last_name: 'Watering',
			email: 'mail@kobuskuch.nl'
		},
		{
			id: 42058115,
			first_name: 'Gijsbert',
			last_name: 'Reenkes',
			email: 'gijsbert_reenkes1337@student.tudelft.nl'
		},
		{
			id: 42229483,
			first_name: 'Gust',
			last_name: 'ter Morsche',
			email: 'gust007@hotmail.com'
		},
		{
			id: 1239053,
			first_name: 'Ronald Christian',
			last_name: 'Pepper',
			email: 'r.c.pepper@sharklasers.com'
		},
		{
			id: 1420532,
			first_name: 'Louise',
			last_name: 'Lindsey',
			email: 'l.lindsey@sharklasers.com'
		},
		{
			id: 2153467,
			first_name: 'Allen Barnabus',
			last_name: 'Couture',
			email: 'a.b.couture@sharklasers.com'
		},
		{
			id: 5673432,
			first_name: 'Julio',
			last_name: 'van Amersfoort',
			email: 'j.vanamersfoort@sharklasers.com'
		},
		{
			id: 8305256,
			first_name: 'Dawn',
			last_name: 'Griffin',
			email: 'd.e.griffin@sharklasers.com'
		}

	];

	state = {
		search: {
			input: '',
			selected: 0,
			result: [
			]
		},
		exam: {
			id: 0,
			name: "Loading...",
			list: [
				{
					id: 0,
					name: 'Midterm 1 5-12',
				},
				{
					id: 1,
					name: 'Midterm 2 5-1'
				},
				{
					id: 2,
					name: 'Final exam 20-2'
				}
			]
		},
		submission: {
			id: 0,
			index: 0,
			input: 0,
			imagePath: test_image,
			list: [
				{
					id: 0,
					checked: true
				},
				{
					id: 1,
					checked: true
				},
				{
					id: 50,
					checked: false
				},
				{
					id: 51,
					checked: false
				},
				{
					id: 64,
					checked: false
				},
				{
					id: 146,
					checked: false
				},
				{
					id: 1465,
					checked: false
				},
				{
					id: 1466,
					checked: false
				},
				{
					id: 1467,
					checked: false
				}
			]
		}
	};

	componentDidMount() {
		api.get('exams')
			.then(exams => {
				this.setState({
					exam: {
						...this.state.exam,
						list: exams
					}
				})
			})
			.catch(err => {
				alert('failed to get exams (see javascript console for details)')
				console.error('failed to get exams:', err)
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
		var unchecked = this.state.submission.list.filter(sub => sub.checked === true).map(sub => sub.id);
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
	nextUnchecked = () => {
		var unchecked = this.state.submission.list.filter(sub => sub.checked === true).map(sub => sub.id);
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
		})
	}

	moveSelection = (event) => {
		if (event.keyCode == 38 || event.keyCode == 40) {
			event.preventDefault();
			var sel = this.state.search.selected;

			if (event.keyCode == 38 && sel > 0) sel--;
			if (event.keyCode == 40 && sel < 8) sel++;

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