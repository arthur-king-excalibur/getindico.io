// This file is part of Indico.
// Copyright (C) 2002 - 2019 CERN
//
// Indico is free software; you can redistribute it and/or
// modify it under the terms of the MIT License; see the
// LICENSE file for more details.

import roomsSpriteURL from 'indico-url:rb.sprite';

import React from 'react';
import PropTypes from 'prop-types';
import {connect} from 'react-redux';

import * as configSelectors from '../common/config/selectors';


const DEFAULT_WIDTH = 290;
const DEFAULT_HEIGHT = 170;

/**
 * This component creates an image based on the "room photo" sprite.
 */
class SpriteImage extends React.Component {
    static propTypes = {
        /** The caching token generated by the server */
        roomsSpriteToken: PropTypes.string.isRequired,
        /** The position of the sprite in the spritesheet */
        pos: PropTypes.number.isRequired,
        /** The height the component should assume */
        height: PropTypes.oneOfType([PropTypes.number, PropTypes.string]),
        /** The width the component should assume */
        width: PropTypes.oneOfType([PropTypes.number, PropTypes.string]),
        /** Additional styles to be applied on the component */
        styles: PropTypes.object,
        /** Whether the image should try to fit vertically instead of horizontally */
        fillVertical: PropTypes.bool,
        /** A function to call when the image gets clicked */
        onClick: PropTypes.func
    };

    static defaultProps = {
        width: DEFAULT_WIDTH,
        height: DEFAULT_HEIGHT,
        styles: {},
        fillVertical: false,
        onClick: null
    };

    constructor(props) {
        super(props);
        this.containerRef = React.createRef();
        this.state = {};
    }

    componentDidMount() {
        // It's OK to call setState(...) here, since the component
        // has to re-render anyway
        //
        // eslint-disable-next-line react/no-did-mount-set-state
        this.setState({
            contHeight: this.containerRef.current.offsetHeight,
            contWidth: this.containerRef.current.offsetWidth
        });
    }

    render() {
        const {pos, width, height, styles, roomsSpriteToken, fillVertical, onClick} = this.props;
        const {contWidth, contHeight} = this.state;

        const imgStyle = {
            backgroundImage: `url(${roomsSpriteURL({version: roomsSpriteToken})}`,
            backgroundPosition: `-${DEFAULT_WIDTH * pos}px 0`,
            backgroundRepeat: 'no-repeat',
            width: DEFAULT_WIDTH,
            height: DEFAULT_HEIGHT,
            transformOrigin: 'top left'
        };

        if (fillVertical) {
            const scale = contHeight / DEFAULT_HEIGHT;
            Object.assign(imgStyle, {
                transform: `translateX(${-((DEFAULT_WIDTH * scale) - contWidth) / 2}px) scale(${scale})`
            });
        } else {
            const scale = contWidth / DEFAULT_WIDTH;
            Object.assign(imgStyle, {
                transform: `translateY(${-((DEFAULT_HEIGHT * scale) - contHeight) / 2}px) scale(${scale})`
            });
        }
        const containerStyle = {
            overflow: 'hidden',
            width,
            height,
            ...styles
        };

        return (
            <div style={containerStyle} ref={this.containerRef}>
                <div style={imgStyle} className="img" onClick={onClick} />
            </div>
        );
    }
}

export default connect(
    state => ({
        roomsSpriteToken: configSelectors.getRoomsSpriteToken(state)
    })
)(SpriteImage);
