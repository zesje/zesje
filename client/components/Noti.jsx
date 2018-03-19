import React from 'react';


class Noti extends React.Component {

    state = {
        messages: [
            {
                title: 'Errorrrrrr!',
                content: 'Omg li la',
                type: 'danger',
                duration: 10,
                closable: true,
                small: true
            }
        ]
    }

    new = (message, options) => {
        console.log(message);
    }

    render() {

        return (
            <div>
            {this.state.messages.map((message, index) => 
                <div className={"notification is-" + message.type} key={index}>
                    <p className="title">{message.title}</p>
                    {message.closable ? <button className="delete"></button> : null}
                    {message.content}
                </div>
            )}
            </div>
        )
    }


}


export default Noti;

