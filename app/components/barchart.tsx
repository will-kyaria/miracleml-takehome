"use client";

import React from 'react';
import { BarChart, Bar, XAxis, YAxis, Tooltip, ResponsiveContainer, Legend } from 'recharts';

interface BarChartProps<T> {
    data: T[];
    dataKeyX: keyof T;
    dataKeyY: keyof T;
    title: string;
}

const BarChartComponent = <T extends object>({ data, dataKeyX, dataKeyY, title }: BarChartProps<T>) => {
    return (
        <div className='bg-white shadow-md rounded-lg flex flex-col p-4'>
            <h1 className="text-xl font-semibold mb-4 text-center">{title}</h1>
            <ResponsiveContainer width="100%" height="100%">
                <BarChart data={data}>
                    <XAxis dataKey={dataKeyX as string} />
                    <YAxis />
                    <Tooltip />
                    <Legend />
                    <Bar dataKey={dataKeyY as string} fill="#8884d8" />
                </BarChart>
            </ResponsiveContainer>
        </div>
    );
};

export default BarChartComponent;
