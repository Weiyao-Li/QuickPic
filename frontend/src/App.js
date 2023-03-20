import React, { useRef } from 'react';
import AWS from 'aws-sdk';
import axios from 'axios';
import styles from './App.css';
import voiceSearch from './component/voiceSearch';
import textSearch from "./component/textSearch";

function App() {
    const searchQueryRef = useRef();
    const uploadedFileRef = useRef();
    const customLabelsRef = useRef();

    return (
        <>
            <head>
                <link
                    href="https://fonts.googleapis.com/icon?family=Material+Icons"
                    rel="stylesheet"
                />
            </head>
            <center>
                <header className={styles.photos_title}>Photos Library</header>
            </center>
            <body>
            <div className="container-fluid">
                <center>
                    <form id="search_photos">
                        <input
                            ref={searchQueryRef}
                            name="search_query"
                            id="search_query"
                            type="text"
                            placeholder="Search Photos Library"
                            autoComplete="off"
                            autoFocus
                        />
                        <button type="button">
                            <i
                                className="large material-icons"
                                id="mic_search"
                                onClick={voiceSearch}
                            >
                                mic
                            </i>
                        </button>
                    </form>
                    <p className={styles.search_info}>
                        Click the microphone to start or stop recording.
                    </p>
                    <div className="row">
                        <button
                            type="button"
                            id="searchPhotos"
                            name="searchPhotos"
                            style={{ width: '100px', height: '25px' }}
                            onClick={textSearch}
                        >
                            Search
                        </button>
                    </div>
                </center>
            </div>
            <div className="row">
                <div id="photos_search_results"></div>
            </div>
            <div className={styles.Upload_files}>
                <h2 style={{ textAlign: 'center' }}>Upload Photos</h2>
                <center>
                    <form action="/action_page.php">
                        <input
                            type="file"
                            id="uploaded_file"
                            name="filename"
                            ref={uploadedFileRef}
                        />
                        <input
                            type="text"
                            id="custom_labels"
                            name="custom_labels"
                            placeholder="Custom labels"
                            ref={customLabelsRef}
                        />
                    </form>
                    <button id="upload_files" onClick={uploadPhoto}>
                        Upload
                    </button>
                </center>
            </div>
            </body>
        </>
    );
}

export default App;
