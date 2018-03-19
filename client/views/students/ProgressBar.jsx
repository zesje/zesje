import React from 'react';

const ProgressBar = (props) => {
    const total = props.submissions.length;
    const checked = props.submissions.filter(sub => sub.validated).length;
    const percentage = ((checked / total) * 100).toFixed(1);

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

export default ProgressBar;