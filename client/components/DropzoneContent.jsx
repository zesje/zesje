import React from 'react'

// const DropzoneContent = (props) => (
//   <div className={'file has-name is-boxed' + (props.center ? ' is-centered' : '')}>
//     <label className='file-label'>
//       <span className='file-cta'>
//         <span className='file-icon'>
//           <i className='fa fa-upload' />
//         </span>
//         <span className='file-label'>
//           {props.text}
//         </span>
//       </span>
//     </label>
//   </div>
// )

const DropzoneContent = ({getRootProps, getInputProps}) => (
  <section>
  <div {...getRootProps()}>
    <input {...getInputProps()} />
    <p>Drag 'n' drop some files here, or click to select files</p>
  </div>
  </section>
)

export default DropzoneContent
