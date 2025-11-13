import React, { useRef, useEffect, useState } from 'react';
import { FaEraser } from 'react-icons/fa';
import Core2 from './../Components/Core2'
import { Link } from 'react-router-dom';

const DrawingCanvas = () => {
    const canvasRef = useRef(null);
    const isDrawing = useRef(false);
    const ctxRef = useRef(null);
    const synthRef = useRef(window.speechSynthesis);
    const utteranceRef = useRef(null);
    
    const [strokeColor, setStrokeColor] = useState('white');
    const [lineWidth, setLineWidth] = useState(5);
    const [isEraser, setIsEraser] = useState(false);
    const [isSpeaking, setIsSpeaking] = useState(false);
    const [selectedColor, setSelectedColor] = useState('white');
    const [isModalOpen, setIsModalOpen] = useState(false);
    const [loading, setLoading] = useState(false);
    const [answer, setAnswer] = useState(""); 

    useEffect(() => {
        const canvas = canvasRef.current;
        canvas.width = window.innerWidth;
        canvas.height = window.innerHeight;

        const context = canvas.getContext('2d');
        context.fillStyle = 'rgba(17, 17, 17, 0.99)';
        context.fillRect(0, 0, canvas.width, canvas.height);
        ctxRef.current = context;

        document.body.style.overflow = 'hidden';

        const handleResize = () => {
            canvas.width = window.innerWidth;
            canvas.height = window.innerHeight;
            resetCanvas();
        };

        window.addEventListener('resize', handleResize);

        return () => {
            window.removeEventListener('resize', handleResize);
            document.body.style.overflow = 'auto';
            // Cleanup speech synthesis on unmount
            if (synthRef.current.speaking) {
                synthRef.current.cancel();
            }
        };
    }, []);

    const stopSpeech = () => {
        if (synthRef.current.speaking) {
            synthRef.current.cancel(); 
            setIsSpeaking(false);
        }
    };

    const speakText = (text) => {
        // Cancel any ongoing speech
        if (synthRef.current.speaking) {
            synthRef.current.cancel();
        }

        // Create new utterance
        utteranceRef.current = new SpeechSynthesisUtterance(text);
        utteranceRef.current.lang = "en-US"; 
        utteranceRef.current.rate = 1;
        utteranceRef.current.pitch = 1;

        // Event handlers
        utteranceRef.current.onstart = () => {
            setIsSpeaking(true);
        };
        
        utteranceRef.current.onend = () => {
            setIsSpeaking(false);
        };

        utteranceRef.current.onerror = (event) => {
            console.error('Speech synthesis error:', event);
            setIsSpeaking(false);
        };

        // Start speaking
        synthRef.current.speak(utteranceRef.current);
    };

    const startDrawing = (e) => {
        isDrawing.current = true;
        draw(e);
    };

    const stopDrawing = () => {
        isDrawing.current = false;
        ctxRef.current.beginPath();
    };

    const draw = (e) => {
        if (!isDrawing.current) return;

        const canvas = canvasRef.current;
        const rect = canvas.getBoundingClientRect();
        const x = e.clientX - rect.left;
        const y = e.clientY - rect.top;

        ctxRef.current.lineWidth = lineWidth;
        ctxRef.current.lineCap = 'round';
        ctxRef.current.strokeStyle = isEraser ? 'rgba(17, 17, 17, 0.99)' : strokeColor;

        ctxRef.current.lineTo(x, y);
        ctxRef.current.stroke();
        ctxRef.current.beginPath();
        ctxRef.current.moveTo(x, y);
    };

    const handleThicknessChange = (e) => {
        setLineWidth(e.target.value);
    };

    const handleColorChange = (color) => {
        setStrokeColor(color);
        setSelectedColor(color);
        setIsEraser(false);
    };

    const resetCanvas = () => {
        const canvas = canvasRef.current;
        ctxRef.current.clearRect(0, 0, canvas.width, canvas.height);
        ctxRef.current.fillStyle = 'rgba(17, 17, 17, 0.99)';
        ctxRef.current.fillRect(0, 0, canvas.width, canvas.height);
        setAnswer("");
        stopSpeech(); // Stop speech when resetting
    };

    const toggleEraser = () => {
        setIsEraser(!isEraser);
    };

    const openModal = () => {
        setIsModalOpen(true);
    };

    const closeModal = () => {
        setIsModalOpen(false);
    };

    const calculateDrawing = async () => {
        const canvas = canvasRef.current;
        const imageDataURL = canvas.toDataURL('image/png');

        setLoading(true);

        try {
            const response = await fetch('http://localhost:8000/save-image', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({ 
                    image: imageDataURL,
                    prompt: "Analyze this mathematical expression and provide a clear solution"
                }),
            });

            const result = await response.json();
            
            if (response.ok) {
                const responseText = result.result || result.analysis || result.response || "No response received";
                
                // Clear canvas
                resetCanvas();
                
                // Set answer
                setAnswer(responseText);

                // Speak the response
                speakText(responseText);
            } else {
                const errorMsg = result.detail || result.message || 'Failed to process image';
                console.error('Failed to save image:', errorMsg);
                setAnswer(`Error: ${errorMsg}`);
                speakText(`Error: ${errorMsg}`);
            }
        } catch (error) {
            console.error('Error:', error);
            const errorMsg = 'Failed to connect to server';
            setAnswer(errorMsg);
            speakText(errorMsg);
        } finally {
            setLoading(false);
        }
    };

    return (
        <div className="relative h-screen w-screen">
            <canvas
                ref={canvasRef}
                onMouseDown={startDrawing}
                onMouseUp={stopDrawing}
                onMouseMove={draw}
                className="absolute inset-0"
            />

            {/* Color Palette */}
            <div className="absolute rounded-e-lg bg-gray-700 top-48 left-0 flex flex-col pl-6 pt-4 pb-4 pr-3 space-y-4">
                {['red', 'green', 'blue', 'yellow', 'orange', 'purple', 'black', 'white', 'brown'].map((color) => (
                    <button
                        key={color}
                        className={`w-8 h-8 rounded-full ${selectedColor === color ? 'border-2 border-white' : ''}`}
                        style={{ backgroundColor: color }}
                        onClick={() => handleColorChange(color)}
                    />
                ))}
            </div>

            {/* Top Right Controls */}
            <div className="absolute top-4 right-4 space-x-3">
                <button
                    onClick={resetCanvas}
                    className="bg-red-500 text-white px-4 py-2 rounded hover:bg-red-700"
                >
                    Reset All
                </button>
                <button
                    onClick={calculateDrawing}
                    className={`bg-blue-500 text-white px-4 py-2 rounded hover:bg-blue-700 ${loading ? 'opacity-50 cursor-not-allowed' : ''}`}
                    disabled={loading}
                >
                    {loading ? 'Calculating...' : 'Calculate'}
                </button>
            </div>

            {/* Thickness Slider */}
            <div className="absolute top-0 pt-5 rounded-b-lg bg-gray-700 w-80 px-7 pb-3 left-1/2 transform -translate-x-1/2">
                <input
                    type="range"
                    min="1"
                    max="20"
                    value={lineWidth}
                    onChange={handleThicknessChange}
                    className="w-full"
                />
                <label className="text-white">Thickness: {lineWidth}px</label>
            </div>

            {/* Eraser Button */}
            <div className="absolute top-32 left-2">
                <button
                    onClick={toggleEraser}
                    className={`bg-gray-500 text-white px-4 pl-5 py-4 rounded hover:bg-gray-700 flex items-center ${isEraser ? 'ring-2 ring-white' : ''}`}
                >
                    <FaEraser className="mr-2" />
                </button>
            </div>

            {/* Details Button */}
            <div className="absolute top-4 left-4 space-x-3">
                <button 
                    onClick={openModal}
                    className="bg-yellow-500 text-white px-4 py-2 rounded hover:bg-yellow-700"
                >
                    Details
                </button>
            </div>

            {/* Answer Display */}
            {answer && (
                <div className="absolute bg-black/80 backdrop-blur-sm text-white text-lg p-6 rounded-lg max-w-2xl" 
                     style={{ left: '50%', top: '50%', transform: 'translate(-50%, -50%)' }}>
                    <div className="whitespace-pre-wrap">{answer}</div>
                </div>
            )}

            {/* Stop Speech Button */}
            {isSpeaking && (
                <div className="absolute bottom-8 left-1/2 transform -translate-x-1/2">
                    <button 
                        onClick={stopSpeech}
                        className="bg-red-600 hover:bg-red-700 text-white px-8 py-4 rounded-full shadow-lg flex items-center space-x-2 animate-pulse"
                    >
                        <svg 
                            className="w-6 h-6" 
                            fill="none" 
                            stroke="currentColor" 
                            viewBox="0 0 24 24"
                        >
                            <rect x="6" y="4" width="4" height="16" />
                            <rect x="14" y="4" width="4" height="16" />
                        </svg>
                        <span className="font-bold text-lg">Stop AI Voice</span>
                    </button>
                </div>
            )}

            {/* Loading Indicator */}
            {loading && (
                <div className="absolute bottom-8 left-1/2 transform -translate-x-1/2">
                    <div className="bg-blue-600 text-white px-6 py-3 rounded-full shadow-lg">
                        <div className="flex items-center space-x-3">
                            <div className="animate-spin rounded-full h-5 w-5 border-b-2 border-white"></div>
                            <span>Processing your drawing...</span>
                        </div>
                    </div>
                </div>
            )}
        </div>
    );
};

export default DrawingCanvas;