import React from 'react';

const EmptyPDF = (props) => {
    let width
    let height
    switch (props.format) {
        case 'a4':
        case 'A4':
        default:
            width = 595
            height = 841
    }

    return (
        <div
            style={{
                paddingTop: '4rem',
                minWidth: (width) + 'px',
                minHeight: (height) + 'px',
                backgroundColor: 'white',
            }}
            className={'has-text-centered'}
        >
            <i className={'fa fa-refresh fa-spin'}></i>
        </div>
    )
}

export default EmptyPDF
