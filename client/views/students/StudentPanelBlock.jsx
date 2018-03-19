import React from 'react';

const StudentPanelBlock = (props) => {

    let panelClass = "panel-block";
    const button = props.selected || props.matched;

    if (button) {
        panelClass += " button";
        panelClass += (props.matched) ? " is-success" : " is-link";
    } else panelClass += " is-active";

    if (props.selected && props.submission > -1) console.log(props.submission)

    return (
        <div key={props.student.id}>
            <a className={panelClass}
                key={props.student.id} id={props.student.id} selected={props.selected} onClick={props.selectStudent}>
                <span className={"panel-icon" + (button ? " has-text-white" : "")}>
                    <i className="fa fa-user"></i>
                </span>
                {props.student.firstName + ' ' + props.student.lastName}
            </a>

            <div className={"panel-block" + (props.selected ? " is-info" : " is-hidden")}
                key="info" style={{ backgroundColor: '#dbdbdb' }}>

                <a className="panel-icon" onClick={() => props.editStudent(props.student)}>
                    <i className="fa fa-database"></i>
                </a>
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

export default StudentPanelBlock;