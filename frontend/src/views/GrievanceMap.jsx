import React, {useEffect, useState} from "react";
import {MapContainer, TileLayer, Marker, Popup} from "react-leaflet";
import MarkerClusterGroup from "react-leaflet-cluster";
import L from "leaflet";
import { grievancesApi} from "../api";
import "leaflet/dist/leaflet.css";

const GrievanceMap = () => {
    const [grievances , setGrievances] = useState([]);

    useEffect(() => {
        loadMapData();
    }, []);

    const loadMapData = async () => {
        try {
            const response = await grievancesApi.getMapData();
            const data = Array.isArray(response)?response: response.data;
            console.log("Map data:", data);
            
            setGrievances(data);
        } catch(err) {
            console.error("Error loading map data:", err);
        }
    };
    const getColor = (status) => {
        switch (status?.toLowerCase()) {
            case "open": return "red";
            case "in_progress": return "orange";
            case "resolved": return "green";
            case "escalated": return "purple";
            default: return "blue";
        }
    };
    const markerIcon = (status) =>
        L.divIcon({
            className: "custom-marker",
            html:  `<div style="
            background:${getColor(status)};
            width:14px;
            height:14px;
            border-radius:50%;
            border: 2px solid white;
            box-shadow: 0 0 4px rgba(0,0,0,0.4);
            "></div>`,
            iconSize: [16,16],
            iconAnchor: [8, 8],
        });
    return (
        <div className="h-screen w-full">
            <MapContainer
                center={[20.5937, 78.9629]}
                zoom={5}
                style={{height: "100%", width:"100%"}}
            >
                <TileLayer
                attribution='&copy; <a href="https://www.openstreetmap.org/copyright">
                OpenStreetMap </a> contributors'
                url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png"
                />
                <MarkerClusterGroup>
                    {grievances.map((g)=>
                    g.latitude && g.longitude ? (
                        <Marker
                        key = {g.id || g._id}
                        position={[parseFloat(g.latitude), parseFloat(g.longitude)]}
                        icon={markerIcon(g.status)}
                        >
                            <Popup>
                                <div className="p-1">
                                    <h3 className="font-bold border-b mb-1">{g.category}</h3>
                                    <p className="text-xs">
                                        <strong>
                                        Status:
                                        </strong>
                                        {g.status}
                                    </p>
                                    <p className="text-xs">
                                        <strong>
                                        Severity:
                                        </strong>
                                        {g.severity}
                                    </p>
                                    <p className="text-xs">
                                        <strong>
                                        Authority:
                                        </strong>
                                        {g.assigned_authority}
                                    </p>
                                    
                                    
                                </div>
                            </Popup>
                        </Marker>
                    ): null
                    )}
                </MarkerClusterGroup>
            </MapContainer>
        </div>
    );
};
export default GrievanceMap;