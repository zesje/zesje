import React from 'react';

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

export default ExamSelector;