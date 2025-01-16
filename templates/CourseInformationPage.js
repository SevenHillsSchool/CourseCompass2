import React from "react";
import "../styling/App.css"; 

const CourseInformationPage = () => {
  // Sample data structure for unit objectives and student skills
  const objectives = [
    {
      title: "Course Name: Unit Name",
      description:
        "Unit Description with Unit objectives",
      details: [
        {
          id: "Topic-1",
          text: "Students should be able to demonstrate basic knowledge of one aspect of unit objectives…",
        },
        {
          id: "Topic-2",
          text: "Students should be able to describe how something in Unit 1…",
        },
        {
          id: "Topic-3",
          text: "Students should be able to compare the benefits and limitations of…",
        },
        {
          id: "Topic-4",
          text: "Students should be able to examine...",
        },
        {
          id: "Topic-5",
          text: "Students should be able to describe...",
        },
      ],
    },
  ];

  return (
    <div className="course-page">
      <h1>Unit Objectives</h1>
      <div className="objective-section">
        {objectives.map((objective, index) => (
          <div key={index} className="objective">
            <h2>{objective.title}</h2>
            <p>{objective.description}</p>
            {objective.details.map((detail) => (
              <div key={detail.id} className="detail-card">
                <h3>{detail.id}</h3>
                <p>{detail.text}</p>
              </div>
            ))}
          </div>
        ))}
      </div>
    </div>
  );
};

export default CourseInformationPage;